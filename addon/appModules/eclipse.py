# eclipse.py
# A part of DBeaver-eclipse-nvda add-on for NVDA
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2021-2025 Jean Braz <jeanbrazcosta@gmail.com>
# Based on original work by Alberto Zanella <lapostadialberto@gmail.com>

"""
eclipseEnhance - NVDA Addon that improves access to the Eclipse IDE

This add-on enhances speech and braille support in Eclipse IDE by:
- Playing distinct sounds for errors and warnings
- Announcing breakpoints during debugging
- Improving code completion suggestions
- Providing better console control
"""

import os
import logging
from typing import Dict, List, Optional

from scriptHandler import script
import addonHandler
import eventHandler
import controlTypes
from comtypes import COMError
import nvwave
import tones
import api
import textInfos
import braille
from NVDAObjects.behaviors import EditableTextWithAutoSelectDetection as Edit
from NVDAObjects.IAccessible import IA2TextTextInfo
import globalCommands
import globalVars
import ui
import oleacc
import winUser
import mouseHandler
import speech
from nvdaBuiltin.appModules import eclipse as base_eclipse

try:
	from nvdaBuiltin.appModules.eclipse import AutocompletionListItem
except ImportError:
	AutocompletionListItem = None

# Initialize translations - this makes the '_' function available
addonHandler.initTranslation()

log = logging.getLogger(__name__)

# Add-on constants
ADDON_NAME = "eclipseEnhance"
PLUGIN_DIR = os.path.abspath(os.path.join(globalVars.appArgs.configPath, "addons", ADDON_NAME))

# Color constants for highlighting detection (RGB values in format: rgb(R, G, B))
RGB_ERROR = 'rgb(255, 0, 128)'
RGB_WARNING = 'rgb(244, 20, 45)'
RGB_BREAKPOINT = 'rgb(0, 0, 255)'
RGB_DEBUG = 'rgb(198, 219, 174)'

class SelectionChangeTextInfo(IA2TextTextInfo) :
	"""Text info that tracks selection changes for word movement."""
	
	def expand(self, unit) :
		"""Expand the text range and track the caret offset."""
		super().expand(unit)
		self._startOffset = self._getCaretOffset()

class EclipseTextArea(base_eclipse.EclipseTextArea,Edit):
	"""Enhanced text area for Eclipse with support for errors, warnings, and breakpoints."""
	
	oldpos = -1
	
	def _caretMovementScriptHelper(self, gesture, unit) :
		"""Helper for caret movement scripts that tracks selection for word movement."""
		orig_tx = self.TextInfo
		if unit == textInfos.UNIT_WORD : 
			self.TextInfo = SelectionChangeTextInfo
		super(EclipseTextArea,self)._caretMovementScriptHelper(gesture, unit)
		self.TextInfo = orig_tx
	
	def event_gainFocus(self) :
		"""Handle focus gain event."""
		super(EclipseTextArea,self).event_gainFocus()
		try:
			tx = self.makeTextInfo(textInfos.POSITION_SELECTION)
			self.processLine(tx)
		except Exception as e:
			log.debug(f"Error processing line on focus: {e}")
		
	def reportFocus(self):
		"""Report focus, handling special case for suggestions."""
		if(self.appModule.lastFocusOnSuggestions) :
			self.appModule.lastFocusOnSuggestions = False
			self._reportText()
			return
		super(EclipseTextArea,self).reportFocus()

	def _reportText(self):
		"""Report the current line or selection."""
		tx = self.makeTextInfo(textInfos.POSITION_SELECTION)
		if not tx.isCollapsed:
			# Translators: This is spoken to indicate what has been selected. for example 'selected hello world'
			speech.speakSelectionMessage(_("selected %s"),tx.text)
		else:
			tx.expand(textInfos.UNIT_LINE)
			speech.speakTextInfo(tx,unit=textInfos.UNIT_LINE,reason=controlTypes.OutputReason.CARET)
		
	def event_caret(self) :
		"""Handle caret movement events."""
		super(Edit, self).event_caret()
		super(base_eclipse.EclipseTextArea, self).event_caret()
		if self is api.getFocusObject() and not eventHandler.isPendingEvents('gainFocus'):
			self.detectPossibleSelectionChange()
		try :
			tx = self.makeTextInfo(textInfos.POSITION_SELECTION)
			tx.collapse()
			tx.expand(textInfos.UNIT_LINE)
			if self.oldpos == tx._startOffset :
				return
			self.processLine(tx)
		except Exception as e:
			log.debug(f"Error in caret event: {e}")
		
	def processLine(self,tx) :
		"""Process the current line to check for errors, warnings, and breakpoints."""
		self.oldpos = tx._startOffset
		tx.collapse()
		tx.expand(textInfos.UNIT_CHARACTER)
		colors = self._hasBackground([RGB_BREAKPOINT,RGB_DEBUG],tx)
		if colors[RGB_BREAKPOINT] : 
			tones.beep(610,80)
		if colors[RGB_DEBUG] :
			tones.beep(310,160)
		
	def _caretScriptPostMovedHelper(self, speakUnit, gesture, info=None):
		"""Helper for caret script movement that handles special cases."""
		if not info:
			try:
				info = self.makeTextInfo(textInfos.POSITION_CARET)
			except Exception as e:
				log.debug(f"Error making text info: {e}")
				return
		info.expand(textInfos.UNIT_CHARACTER)
		if (speakUnit == textInfos.UNIT_WORD) and (info.text == "\r\n") :
			super(EclipseTextArea,self)._caretScriptPostMovedHelper(textInfos.UNIT_CHARACTER, gesture, info)
		else :
			super(EclipseTextArea,self)._caretScriptPostMovedHelper(speakUnit, gesture, info)
	
	@script(
		description=_("Toggle breakpoint and report state"),
		category="Eclipse",
		gestures=["kb:control+shift+b"]
	)
	def script_breakpointToggle(self,gesture) :
		"""Toggle breakpoint at current line and announce state."""
		colors = self._hasBackground([RGB_BREAKPOINT])
		if(colors[RGB_BREAKPOINT]) : 
			ui.message(_("Breakpoint off"))
		else :
			ui.message(_("Breakpoint on"))
		gesture.send()
	
	@script(
		description=_("Report error or warning at cursor position"),
		category="Eclipse",
		gestures=["kb:control+."]
	)
	def script_errorReport(self,gesture) :
		"""Report errors or warnings at the cursor position."""
		gesture.send()
		colors = self._hasBackground([RGB_ERROR,RGB_WARNING])
		if(colors[RGB_ERROR]) : 
			braille.handler.message(_("error"))
			self.appModule.play_error()
		elif(colors[RGB_WARNING]) :
			braille.handler.message(_("warning"))
			self.appModule.play_warning()
		globalCommands.commands.script_reportCurrentLine(gesture)
	
	@script(
		description=_("Save and report if file contains errors or warnings"),
		category="Eclipse",
		gestures=["kb:control+s"]
	)
	def script_checkAndSave(self,gesture) :
		"""Save the file and report any errors or warnings in the document."""
		gesture.send()
		colors = self._hasBackground([RGB_ERROR,RGB_WARNING],ti=self.makeTextInfo(textInfos.POSITION_ALL))
		if colors[RGB_ERROR] : 
			braille.handler.message(_("saved with errors"))
			self.appModule.play_error()
		elif colors[RGB_WARNING] : 
			braille.handler.message(_("saved with warnings"))
			self.appModule.play_warning()

	def _hasBackground(self, colors: List[str], ti = None):
		"""
		Check if text at given position has specified background colors.
		
		Args:
			colors: List of RGB color strings to search for
			ti: TextInfo object to check. If None, uses current selection.
		
		Returns:
			Dictionary mapping color strings to boolean indicating if found
		"""
		cfg = {
			"detectFormatAfterCursor":False,
			"reportFontName":False,"reportFontSize":False,"reportFontAttributes":False,"reportColor":True,"reportRevisions":False,
			"reportStyle":False,"reportAlignment":False,"reportSpellingErrors":False,
			"reportPage":False,"reportLineNumber":False,"reportTables":False,
			"reportLinks":False,"reportHeadings":False,"reportLists":False,
			"reportBlockQuotes":False,"reportComments":False,
		}
		retval = dict((color,False) for color in colors)
		if not ti :
			ti = self.makeTextInfo(textInfos.POSITION_SELECTION)
			ti._endOffset = ti._startOffset
			ti.collapse()
			ti.expand(textInfos.UNIT_CHARACTER)
		try:
			formatField=textInfos.FormatField()
			for field in ti.getTextWithFields(cfg):
				if isinstance(field,textInfos.FieldCommand) and isinstance(field.field,textInfos.FormatField):
					if 'background-color' in field.field :
						formatField.update(field.field)
						rgb = formatField['background-color']
						if rgb in retval :
							retval[rgb] = True
		except Exception as e:
			log.debug(f"Error checking background colors: {e}")
		return retval
	
	
class AppModule(base_eclipse.AppModule):
	"""App module for Eclipse IDE with enhanced accessibility features."""
	
	terminateButton = None
	openConsoleButton = None
	pinConsoleButton = None
	lastFocusOnSuggestions = False

	def _get_statusBar(self):
		"""Get the Eclipse status bar object."""
		foreground = api.getForegroundObject()
		obj = foreground.simpleFirstChild

		while obj:
			if obj.role == controlTypes.Role.STATUSBAR:
				return obj.simpleFirstChild

			obj = obj.simpleNext

		return None

	def get_tool_button(self, myAccName, myAccRole, myObj):
		"""
		Find a toolbar button in the Console view by accessible name and role.
		
		Args:
			myAccName: Accessible name to search for (can be None)
			myAccRole: Accessible role constant
			myObj: Current button object (if already found)
		
		Returns:
			The button object if found, otherwise None
		"""
		if myObj != None : 
			return myObj
		obj = api.getFocusObject()
		while (obj.parent is not None) :
			if (obj.role == controlTypes.Role.TABCONTROL) and (obj.name == 'Console') :
				break
			obj = obj.parent
		if obj.name != "Console" : 
			return myObj
		obj = obj.firstChild
		while obj :
			objs = obj
			while objs and objs.role != controlTypes.Role.TOOLBAR :
				objs = objs.firstChild
			obj = obj.next
			if not objs : 
				continue
			try:
				for i in range(1,objs.childCount+1) :
					if objs.IAccessibleObject.accRole(i) == myAccRole and objs.IAccessibleObject.accName(i) == myAccName : 
						return objs.children[i-1]
			except Exception as e:
				log.debug(f"Error searching toolbar buttons: {e}")
		
		if myAccName == "Terminate" : #Terminate button may have no accName
			return self.get_tool_button(None,myAccRole,myObj)
		return myObj
	
	def get_terminate_button(self) :
		"""Get the Terminate button from the Console toolbar."""
		self.terminateButton = self.get_tool_button("Terminate", oleacc.ROLE_SYSTEM_PUSHBUTTON, self.terminateButton)
		
	def get_open_console_button(self) :
		"""Get the Open Console button from the Console toolbar."""
		self.openConsoleButton = self.get_tool_button("Open Console", oleacc.ROLE_SYSTEM_SPLITBUTTON, self.openConsoleButton)
	
	def get_pin_console_button(self) :
		"""Get the Pin Console button from the Console toolbar."""
		self.pinConsoleButton = self.get_tool_button("Pin Console", oleacc.ROLE_SYSTEM_CHECKBUTTON, self.pinConsoleButton)
	
	def event_gainFocus(self,obj,nh):
		"""Handle focus gain, filtering out unwanted focus events."""
		if obj.role == controlTypes.Role.PANE and self.lastFocusOnSuggestions :
			return
		nh()
	
	def event_focusEntered(self,obj,nh):
		"""Handle focus entered, filtering out unwanted focus events."""
		if obj.role == controlTypes.Role.TABCONTROL and self.lastFocusOnSuggestions :
			return
		nh()
	
	def event_NVDAObject_init(self, obj):
		"""Initialize NVDAObjects with custom handling."""
		super(AppModule, self).event_NVDAObject_init(obj)
		
		if obj.role == controlTypes.Role.DIALOG and "show Template Proposals" in obj.description :
			# Remove annoying tooltips
			obj.description = ""
			self.lastFocusOnSuggestions = True
		
		if obj.windowClassName == "SysListView32" and obj.role == controlTypes.Role.LISTITEM:
			if(isinstance(api.getFocusObject(),  EclipseTextArea)) :
				self.play_suggestions()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		"""Select appropriate classes for NVDAObjects."""
		super(AppModule, self).chooseNVDAObjectOverlayClasses(obj, clsList)
		if obj.windowClassName == "SWT_Window0" and obj.role == controlTypes.Role.EDITABLETEXT:
			clsList.remove(base_eclipse.EclipseTextArea)
			clsList.insert(0, EclipseTextArea)
		# Autocompletion items are placed outside the main eclipse window
		if (
				AutocompletionListItem is not None and
				AutocompletionListItem not in clsList and
				obj.role == controlTypes.Role.LISTITEM
				and obj.parent.parent.parent.role == controlTypes.Role.DIALOG
				and obj.parent.parent.parent.simpleParent == api.getDesktopObject()
				and obj.parent.parent.parent.parent.simpleNext.role in (
					controlTypes.Role.BUTTON,
					controlTypes.Role.TOGGLEBUTTON
				)
			):
				clsList.insert(0, AutocompletionListItem)

	def _play_sound(self, sound_filename: str) -> None:
		"""
		Play a sound file from the addon's sounds directory.
		
		Args:
			sound_filename: Name of the sound file (e.g., "error.wav")
		"""
		try:
			sound_path = os.path.join(PLUGIN_DIR, "sounds", sound_filename)
			if os.path.exists(sound_path):
				nvwave.playWaveFile(sound_path)
			else:
				log.warning(f"Sound file not found: {sound_path}")
		except Exception as e:
			log.error(f"Error playing sound {sound_filename}: {e}")

	def play_suggestions(self) :
		"""Play sound notification for code completion suggestions."""
		self._play_sound("suggestions.wav")
	
	def play_error(self) :
		"""Play sound notification for errors."""
		self._play_sound("error.wav")
	
	def play_warning(self) :
		"""Play sound notification for warnings."""
		self._play_sound("warn.wav")
	
	
	@script(
		description=_("Click the Open Console toolbar button"),
		category="Eclipse",
		gestures=["kb:nvda+shift+o"]
	)
	def script_clickOpenConsoleButton(self, gesture) :
		"""Click the Open Console button in the Console toolbar."""
		self.get_open_console_button()
		if self.openConsoleButton != None :
			try :
				self.openConsoleButton.doAction()
			except Exception as e:
				log.debug(f"Error clicking Open Console button: {e}")

	@script(
		description=_("Click the Pin Console toolbar button"),
		category="Eclipse",
		gestures=["kb:nvda+shift+p"]
	)
	def script_clickPinConsoleButton(self, gesture) :
		"""Click the Pin Console button in the Console toolbar."""
		self.get_pin_console_button()
		if self.pinConsoleButton != None :
			try :
				oldX,oldY = winUser.getCursorPos()
				winUser.setCursorPos(self.pinConsoleButton.location.left,self.pinConsoleButton.location.top)
				#perform Mouse Left-Click
				mouseHandler.executeMouseEvent(winUser.MOUSEEVENTF_LEFTDOWN,0,0)
				mouseHandler.executeMouseEvent(winUser.MOUSEEVENTF_LEFTUP,0,0)
				winUser.setCursorPos(oldX,oldY)
				if controlTypes.State.CHECKED in self.pinConsoleButton.states :
					ui.message(_("Pin Console")+" "+_("not checked"))
				else :
					ui.message(_("Pin Console")+" "+_("checked"))
			except Exception as e:
				log.debug(f"Error clicking Pin Console button: {e}")

	
	@script(
		description=_("Click the Terminate toolbar button"),
		category="Eclipse",
		gestures=["kb:NVDA+shift+t"]
	)
	def script_clickTerminateButton(self, gesture):
		"""Click the Terminate button in the Console toolbar."""
		self.get_terminate_button()
		if self.terminateButton != None :
			try :
				self.terminateButton.doAction()
				ui.message(_("Terminated"))
			except Exception as e:
				log.debug(f"Error clicking Terminate button: {e}")
	

	def script_braille_scrollBack(self, gesture):
		"""Handle braille scroll back, with fallback for COM errors."""
		try :
			globalCommands.commands.script_braille_scrollBack(gesture)
		except COMError :
			globalCommands.commands.script_braille_previousLine(gesture)
