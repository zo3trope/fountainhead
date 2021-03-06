# -*- Mode:python c-file-style:"gnu" indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014-2015 Regents of the University of California.
# Author: Zhehao Wang <wangzhehao410305gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.

# This module defines the HTML generator class for parsed fountain scripts.
# Ported to Python from objc in nyousefi/Fountain repository

# For HTML output, paginator is ignored right now.

import re
import sys

from fountain_parser import ParserVersion
from regex_rules import *

class FountainHTMLGenerator(object):
    def __init__(self, script, cssFile = '', componentParent = 'components', version = ParserVersion.DEFAULT):
        self._script = script
        self._bodyText = ''
        self._cssFile = cssFile
        self._componentParent = componentParent.rstrip('/') + '/'
        
        self._version = version
        if self._version == ParserVersion.REMAP:
            self._fountainRegex = FountainRegexRemap()
            self.generateHtml = self.generateHtmlRemap
            self._componentList = []
        elif self._version == ParserVersion.BASE:
            self._fountainRegex = FountainRegexBase()
            self.generateHtml = self.generateHtmlBase
        else:
            # Right now using remap as default; DEFAULT value was not really useful, 
            # since self._fountainRegex is using Remap class
            self._version == ParserVersion.DEFAULT
            self._fountainRegex = FountainRegexRemap()
            self.generateHtml = self.generateHtmlRemap
            self._componentList = []
        return
    
    # HTML class is elementType with spaces replaced by dashes
    def htmlClassForType(self, elementType):
        return re.sub(" ", "-", elementType.lower())
    
    def generateHtmlBase(self):
        if (self._bodyText == ''):
            self._bodyText = self.bodyForScriptBase()
        html = '<!DOCTYPE html>\n<html>\n<head>\n'
        if (self._cssFile != ''):
            html += '<link rel=\"stylesheet\" type=\"text/css\" href=\"' + self._cssFile + '\">\n'
        # Note: here a <section> tag is added by default.
        html += '</head>\n<body>\n<section>\n' + self._bodyText + '</section>\n</body>\n</html>\n'
        return html
    
    def generateHtmlRemap(self):
        if (self._bodyText == ''):
            self._bodyText = self.bodyForScriptRemap()
        html = '<!DOCTYPE html>\n<html>\n<head>\n'
        if (self._cssFile != ''):
            html += '<link rel=\"stylesheet\" type=\"text/css\" href=\"' + self._cssFile + '\">\n'
        # bodyForScript fills self._componentList; Right now, components are supposed to end with a .html
        for componentName in self._componentList:
            html += '<link rel=\"import\" href=\"' + self._componentParent + componentName + '.html\">\n'
        # Note: here a <section> tag is added by default.
        html += '</head>\n<body>\n<section>\n' + self._bodyText + '</section>\n</body>\n</html>\n'
        return html
    
    def bodyForScriptRemap(self):
        bodyText = ''
        # add title page
        titleElements = self._script._titlePageContents
        
        if titleElements:
            bodyText += '<div id=\'' + self._fountainRegex.TITLE_DIV + '\'>'
            
            # Titles
            bodyText += '<p class=\'' + self._fountainRegex.TITLE_TITLE_CLASS + '\'>'
            if titleElements[self._fountainRegex.TITLE_TITLE_STRING]:
                for temp in titleElements[self._fountainRegex.TITLE_TITLE_STRING]:
                    bodyText += temp + '<br>'
            else:
                bodyText += 'Untitled'
            bodyText += '</p>'
                
            # Credit
            bodyText += '<p class=\'' + self._fountainRegex.TITLE_CREDIT_CLASS + '\'>'
            if self._fountainRegex.TITLE_CREDIT_STRING in titleElements:
                for temp in titleElements[self._fountainRegex.TITLE_CREDIT_STRING]:
                    bodyText += temp + '<br>'
            else:
                bodyText += 'written by'
            bodyText += '</p>'
            
            # Authors
            bodyText += '<p class=\'' + self._fountainRegex.TITLE_AUTHOR_CLASS + '\'>'
            if self._fountainRegex.TITLE_AUTHOR_STRING in titleElements:
                for temp in titleElements[self._fountainRegex.TITLE_AUTHOR_STRING]:
                    bodyText += temp + '<br>'
            else:
                bodyText += 'Anonymous'
            bodyText += '</p>'
            
            # Sources
            if self._fountainRegex.TITLE_SOURCE_STRING in titleElements:
                bodyText += '<p class=\'' + self._fountainRegex.TITLE_SOURCE_CLASS + '\'>'
                for temp in titleElements[self._fountainRegex.TITLE_SOURCE_STRING]:
                    bodyText += temp + '<br>'
                bodyText += '</p>'
            
            # Draft date
            if self._fountainRegex.TITLE_DRAFT_DATE_STRING in titleElements:
                bodyText += '<p class=\'' + self._fountainRegex.TITLE_DRAFT_DATE_CLASS + '\'>'
                for temp in titleElements[self._fountainRegex.TITLE_DRAFT_DATE_STRING]:
                    bodyText += temp + '<br>'
                bodyText += '</p>'
            
            # Contact
            if self._fountainRegex.TITLE_CONTACT_STRING in titleElements:
                bodyText += '<p class=\'' + self._fountainRegex.TITLE_CONTACT_CLASS + '\'>'
                for temp in titleElements[self._fountainRegex.TITLE_CONTACT_STRING]:
                    bodyText += temp + '<br>'
                bodyText += '</p>'
            
            bodyText += '</div>'
            
        # Page breaks are not handled in current HTML output
        dialogueTypes = [self._fountainRegex.CHARACTER_TAG_PATTERN, self._fountainRegex.DIALOGUE_TAG_PATTERN, self._fountainRegex.PARENTHETICAL_TAG_PATTERN]
        ignoreTypes = [self._fountainRegex.BONEYARD_TAG_PATTERN, self._fountainRegex.COMMENT_TAG_PATTERN, self._fountainRegex.SYNOPSIS_TAG_PATTERN, self._fountainRegex.SECTION_HEADING_PATTERN]
        
        dualDialogueCharacterCount = 0
        
        elements = self._script._elements
        
        try:
            self._fountainRegex.COMPONENT_PATTERN
        except NameError:
            print('Fountain Regex pattern does not contain definition for Web component. Version mismatch?')
            sys.exit(0)
        else:
            self._componentList = []
            # Flag for whether we are in a component definition, if so, this element should not appear as normal ones
            inComponent = False
            # Flag for whether this component is ready for generation.
            generateComponent = False
            componentName = ''
            componentArgs = dict()
            componentDesc = ''
            
        for element in elements:
            if (element._elementType in ignoreTypes):
                continue
            
            if (element._elementType == self._fountainRegex.PAGE_BREAK_PATTERN):
                bodyText += '</section>\n<section>\n'
                continue
            
            if (element._elementType == self._fountainRegex.CHARACTER_TAG_PATTERN and element._isDualDialogue):
                dualDialogueCharacterCount += 1
                if (dualDialogueCharacterCount == 1):
                    bodyText += '<div class=\'' + self._fountainRegex.DUAL_DIALOGUE_CLASS + '\'>\n'
                    bodyText += '<div class=\'' + self._fountainRegex.DUAL_DIALOGUE_LEFT_CLASS + '\'>\n'
                elif (dualDialogueCharacterCount == 2):
                    bodyText += '<div class=\'' + self._fountainRegex.DUAL_DIALOGUE_RIGHT_CLASS + '\'>\n'
            
            if (dualDialogueCharacterCount >= 2 and not (element._elementType in dialogueTypes)):
                dualDialogueCharacterCount = 0
                bodyText += '</div>\n</div>\n'
            
            text = ''
            if (element._elementType == self._fountainRegex.SCENE_HEADING_PATTERN and element._sceneNumber != None):
                text += '<span class=\'' + self._fountainRegex.SCENE_NUMBER_LEFT + '\'>' + element._sceneNumber + '</span>'
                text += element._elementText
                text += '<span class=\'' + self._fountainRegex.SCENE_NUMBER_RIGHT + '\'>' + element._sceneNumber + '</span>'
            else:
                text += element._elementText
                # Special generation step for component and arguments
                if (element._elementType == self._fountainRegex.COMPONENT_NAME_PATTERN):
                    if (not inComponent):
                        if (element._elementText in self._componentList):
                            pass
                        else:
                            self._componentList.append(element._elementText)
                        componentName = element._elementText
                        inComponent = True
                    else:
                        print('ERROR: Nested component definition in script. Not sure how to parse yet.')
                if (element._elementType == self._fountainRegex.COMPONENT_ARGUMENTS_PATTERN):
                    if (inComponent):
                        args = re.findall(self._fountainRegex.COMPONENT_ARGUMENTS_SPLIT, element._elementText)
                        for arg in args:
                            equalSign = arg.find('=')
                            if (equalSign > 0):
                                argName = arg[:equalSign].strip()
                                argValue = arg[equalSign + 1:].strip()
                                componentArgs[argName] = argValue
                            else:
                                print('WARNING: no equal sign found for component argument; on purpose?')
                if (element._elementType == self._fountainRegex.COMPONENT_DESCRIPTION_PATTERN):
                    if (inComponent):
                        generateComponent = True
                        componentDesc = element._elementText
                        
            if (element._elementType == self._fountainRegex.CHARACTER_TAG_PATTERN and element._isDualDialogue):
                text = re.sub(self._fountainRegex.DUAL_DIALOGUE_ANGLE_MARK_PATTERN, self._fountainRegex.EMPTY_REPLACEMENT, text)
            
            text = re.sub(self._fountainRegex.BOLD_ITALIC_UNDERLINE_PATTERN, self._fountainRegex.BOLD_ITALIC_UNDERLINE_TAG, text)
            text = re.sub(self._fountainRegex.BOLD_ITALIC_PATTERN, self._fountainRegex.BOLD_ITALIC_TAG, text)
            text = re.sub(self._fountainRegex.BOLD_UNDERLINE_PATTERN, self._fountainRegex.BOLD_UNDERLINE_TAG, text)
            text = re.sub(self._fountainRegex.ITALIC_UNDERLINE_PATTERN, self._fountainRegex.ITALIC_UNDERLINE_TAG, text)
            text = re.sub(self._fountainRegex.BOLD_PATTERN, self._fountainRegex.BOLD_TAG, text)
            text = re.sub(self._fountainRegex.ITALIC_PATTERN, self._fountainRegex.ITALIC_TAG, text)
            text = re.sub(self._fountainRegex.UNDERLINE_PATTERN, self._fountainRegex.UNDERLINE_TAG, text)
            text = re.sub(self._fountainRegex.FONT_EMPH_IGNORE_TAG, self._fountainRegex.EMPTY_REPLACEMENT, text)
            
            if (not inComponent):
                if (text != ''):
                    additionalClasses = ''
                    if (element._isCentered):
                        additionalClasses += self._fountainRegex.CENTER_CLASS
                    bodyText += '<p class=\'' + self.htmlClassForType(element._elementType) + additionalClasses + '\'>' + text + '</p>\n'
            elif (generateComponent):
                bodyText += '<' + componentName
                for argName, argValue in componentArgs.items():
                    bodyText += ' ' + argName + '=' + argValue
                bodyText += '>' + componentDesc + '</' + componentName + '>\n'
                
                generateComponent = False
                inComponent = False
                componentName = ''
                componentArgs = dict()
                componentDesc = ''
                
        return bodyText
    
    def bodyForScriptBase(self):
        bodyText = ''
        # add title page
        titleElements = self._script._titlePageContents
        
        if titleElements:
            bodyText += '<div id=\'' + self._fountainRegex.TITLE_DIV + '\'>'
            
            # Titles
            bodyText += '<p class=\'' + self._fountainRegex.TITLE_TITLE_CLASS + '\'>'
            if titleElements[self._fountainRegex.TITLE_TITLE_STRING]:
                for temp in titleElements[self._fountainRegex.TITLE_TITLE_STRING]:
                    bodyText += temp + '<br>'
            else:
                bodyText += 'Untitled'
            bodyText += '</p>'
                
            # Credit
            bodyText += '<p class=\'' + self._fountainRegex.TITLE_CREDIT_CLASS + '\'>'
            if self._fountainRegex.TITLE_CREDIT_STRING in titleElements:
                for temp in titleElements[self._fountainRegex.TITLE_CREDIT_STRING]:
                    bodyText += temp + '<br>'
            else:
                bodyText += 'written by'
            bodyText += '</p>'
            
            # Authors
            bodyText += '<p class=\'' + self._fountainRegex.TITLE_AUTHOR_CLASS + '\'>'
            if self._fountainRegex.TITLE_AUTHOR_STRING in titleElements:
                for temp in titleElements[self._fountainRegex.TITLE_AUTHOR_STRING]:
                    bodyText += temp + '<br>'
            else:
                bodyText += 'Anonymous'
            bodyText += '</p>'
            
            # Sources
            if self._fountainRegex.TITLE_SOURCE_STRING in titleElements:
                bodyText += '<p class=\'' + self._fountainRegex.TITLE_SOURCE_CLASS + '\'>'
                for temp in titleElements[self._fountainRegex.TITLE_SOURCE_STRING]:
                    bodyText += temp + '<br>'
                bodyText += '</p>'
            
            # Draft date
            if self._fountainRegex.TITLE_DRAFT_DATE_STRING in titleElements:
                bodyText += '<p class=\'' + self._fountainRegex.TITLE_DRAFT_DATE_CLASS + '\'>'
                for temp in titleElements[self._fountainRegex.TITLE_DRAFT_DATE_STRING]:
                    bodyText += temp + '<br>'
                bodyText += '</p>'
            
            # Contact
            if self._fountainRegex.TITLE_CONTACT_STRING in titleElements:
                bodyText += '<p class=\'' + self._fountainRegex.TITLE_CONTACT_CLASS + '\'>'
                for temp in titleElements[self._fountainRegex.TITLE_CONTACT_STRING]:
                    bodyText += temp + '<br>'
                bodyText += '</p>'
            
            bodyText += '</div>'
            
        # Page breaks are not handled in current HTML output
        dialogueTypes = [self._fountainRegex.CHARACTER_TAG_PATTERN, self._fountainRegex.DIALOGUE_TAG_PATTERN, self._fountainRegex.PARENTHETICAL_TAG_PATTERN]
        ignoreTypes = [self._fountainRegex.BONEYARD_TAG_PATTERN, self._fountainRegex.COMMENT_TAG_PATTERN, self._fountainRegex.SYNOPSIS_TAG_PATTERN, self._fountainRegex.SECTION_HEADING_PATTERN]
        
        dualDialogueCharacterCount = 0
        
        elements = self._script._elements
        for element in elements:
            if (element._elementType in ignoreTypes):
                continue
            
            if (element._elementType == self._fountainRegex.PAGE_BREAK_PATTERN):
                bodyText += '</section>\n<section>\n'
                continue
            
            if (element._elementType == self._fountainRegex.CHARACTER_TAG_PATTERN and element._isDualDialogue):
                dualDialogueCharacterCount += 1
                if (dualDialogueCharacterCount == 1):
                    bodyText += '<div class=\'' + self._fountainRegex.DUAL_DIALOGUE_CLASS + '\'>\n'
                    bodyText += '<div class=\'' + self._fountainRegex.DUAL_DIALOGUE_LEFT_CLASS + '\'>\n'
                elif (dualDialogueCharacterCount == 2):
                    bodyText += '<div class=\'' + self._fountainRegex.DUAL_DIALOGUE_RIGHT_CLASS + '\'>\n'
            
            if (dualDialogueCharacterCount >= 2 and not (element._elementType in dialogueTypes)):
                dualDialogueCharacterCount = 0
                bodyText += '</div>\n</div>\n'
            
            text = ''
            if (element._elementType == self._fountainRegex.SCENE_HEADING_PATTERN and element._sceneNumber != None):
                text += '<span class=\'' + self._fountainRegex.SCENE_NUMBER_LEFT + '\'>' + element._sceneNumber + '</span>'
                text += element._elementText
                text += '<span class=\'' + self._fountainRegex.SCENE_NUMBER_RIGHT + '\'>' + element._sceneNumber + '</span>'
            else:
                text += element._elementText
                
            if (element._elementType == self._fountainRegex.CHARACTER_TAG_PATTERN and element._isDualDialogue):
                text = re.sub(self._fountainRegex.DUAL_DIALOGUE_ANGLE_MARK_PATTERN, self._fountainRegex.EMPTY_REPLACEMENT, text)
                
            text = re.sub(self._fountainRegex.BOLD_ITALIC_UNDERLINE_PATTERN, self._fountainRegex.BOLD_ITALIC_UNDERLINE_TAG, text)
            text = re.sub(self._fountainRegex.BOLD_ITALIC_PATTERN, self._fountainRegex.BOLD_ITALIC_TAG, text)
            text = re.sub(self._fountainRegex.BOLD_UNDERLINE_PATTERN, self._fountainRegex.BOLD_UNDERLINE_TAG, text)
            text = re.sub(self._fountainRegex.ITALIC_UNDERLINE_PATTERN, self._fountainRegex.ITALIC_UNDERLINE_TAG, text)
            text = re.sub(self._fountainRegex.BOLD_PATTERN, self._fountainRegex.BOLD_TAG, text)
            text = re.sub(self._fountainRegex.ITALIC_PATTERN, self._fountainRegex.ITALIC_TAG, text)
            text = re.sub(self._fountainRegex.UNDERLINE_PATTERN, self._fountainRegex.UNDERLINE_TAG, text)
            text = re.sub(self._fountainRegex.FONT_EMPH_IGNORE_TAG, self._fountainRegex.EMPTY_REPLACEMENT, text)
            
            if (text != ''):
                additionalClasses = ''
                if (element._isCentered):
                    additionalClasses += self._fountainRegex.CENTER_CLASS
                bodyText += '<p class=\'' + self.htmlClassForType(element._elementType) + additionalClasses + '\'>' + text + '</p>\n'
        
        return bodyText
   