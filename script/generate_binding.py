# This script generates a set of runtime OpenGL bindings for API extensions.

nonPortableExtensions = set()

import sys, os, argparse, xml.sax

from enum import Enum

def findNonPortableExtensionSuffixes(extensionDir):
	# https://www.opengl.org/archives/resources/features/OGLextensions/		
	for dirent in os.listdir(extensionDir):
		if not os.path.isdir(os.path.join(extensionDir, dirent)):			
			continue

		if (dirent != 'ARB'):
			nonPortableExtensions.add(dirent)
			print('Excluding API extension suffix: ' + dirent)

class OpenGLRegistryParserState(Enum):
	NONE = 0
	ROOT_NODE = 1
	COMMAND_LIST = 2
	COMMAND = 3
	PROTO = 4
	PROTO_TYPE = 5
	PROTO_NAME = 6	
	EXCLUDED_FEATURE_LIST = 7
	EXCLUDED_FEATURE_LIST_REQUIRE = 8
	INCLUDED_FEATURE_LIST = 9
	INCLUDED_FEATURE_LIST_REQUIRE = 10
	COMMAND_ALIAS = 11

def writeHdrFilePrefix(hdrFile):
	hdrFile.write('#pragma once\n')
	hdrFile.write('\n')
	hdrFile.write('#include <gweekgl/platform.h>\n')			
	hdrFile.write('\n')

	hdrFile.write('#ifdef __cplusplus\n')
	hdrFile.write('extern "C"\n')
	hdrFile.write('{\n')
	hdrFile.write('#endif\n')
	hdrFile.write('\n')
	hdrFile.write('\t/* Needed to trigger binding initialization from the system OpenGL libraries. */\n')
	hdrFile.write('\tvoid gweekgl_initialize();\n')
	hdrFile.write('\n')
	hdrFile.write('/* For some reason, on linux gl.h includes glext.h and defines all the prototypes */\n')
	hdrFile.write('#if !defined(GWEEK_PLATFORM_LINUX)\n')

def writeHdrFileSuffix(hdrFile):
	hdrFile.write('#endif\n')
	hdrFile.write('#ifdef __cplusplus\n')
	hdrFile.write('}\n')
	hdrFile.write('#endif')
	hdrFile.write('\n')

def writeSrcFilePrefix(srcFile):	
	srcFile.write('#include <gweekgl/platform.h>\n')
	srcFile.write('#include <gweekgl/opengl.h>\n')
	srcFile.write('\n')	

def writeSrcFileSuffix(srcFile):
	srcFile.write('\n')

def trackStaticFunctionBinding(srcFile, hdrFile, excludedApiCalls, definedApiCalls, aliasedApiCalls, name, alias):

	for extensionSuffix in nonPortableExtensions:
		if name.endswith(extensionSuffix):
			return

	if name in excludedApiCalls:
		return	

	if name == 'glGetPointerv':
		return # HACK, not sure why the default Chronos headers don't generate this function ptr.

	if not alias:
		definedApiCalls.add(name)
	else:
		aliasedApiCalls[name] = alias

	ptrType = 'PFN' + name.upper() + 'PROC'

	hdrFile.write('\textern ' + ptrType + ' ' + name + ';\n')

def writeBindingImplementation(srcFile, definedApiCalls, aliasedApiCalls):

	undefinedAliases = set()
	for name, alias in aliasedApiCalls.items():
		if alias not in definedApiCalls:
			undefinedAliases.add(name)

	for undefinedAlias in undefinedAliases:
		del aliasedApiCalls[undefinedAlias]

	for apiCall in definedApiCalls:
		ptrType = 'PFN' + apiCall.upper() + 'PROC'
		srcFile.write('' + ptrType + ' ' + apiCall + ';\n')

	for name in aliasedApiCalls.keys():
		ptrType = 'PFN' + name.upper() + 'PROC'
		srcFile.write('' + ptrType + ' ' + name + ';\n')

	srcFile.write('\n');
	srcFile.write('void gweekgl_initialize()\n')
	srcFile.write('{\n');

	for apiCall in definedApiCalls:
		ptrType = 'PFN' + apiCall.upper() + 'PROC'
		srcFile.write('\t' + apiCall + ' = (' + ptrType + ')(GWEEK_PROC_ADDR_FUNC("' + apiCall + '"));\n')

	for name, alias in aliasedApiCalls.items():
		ptrType = 'PFN' + name.upper() + 'PROC'
		srcFile.write('\t' + name + ' = (' + ptrType + ')(' + alias + ');\n')

	srcFile.write('}\n')

class OpenGLRegistryExclusions(xml.sax.ContentHandler):

	def __init__(self, exclusionSet, inclusionSet):
		self.state = OpenGLRegistryParserState.NONE	
		self.exclusionSet = exclusionSet
		self.inclusionSet = inclusionSet
	
	def startElement(self, name, attrs):
		if name == "registry" and self.state == OpenGLRegistryParserState.NONE:
			self.state = OpenGLRegistryParserState.ROOT_NODE
		if name == "feature" and self.state == OpenGLRegistryParserState.ROOT_NODE:
			api = attrs['api']
			featureVersion = attrs['name']

			if api != 'gl' or featureVersion == 'GL_VERSION_1_0' or featureVersion == 'GL_VERSION_1_1':
				self.state = OpenGLRegistryParserState.EXCLUDED_FEATURE_LIST
			else:			
				self.state = OpenGLRegistryParserState.INCLUDED_FEATURE_LIST

		if name == "require" and self.state == OpenGLRegistryParserState.EXCLUDED_FEATURE_LIST:
			self.state = OpenGLRegistryParserState.EXCLUDED_FEATURE_LIST_REQUIRE

		if name == "require" and self.state == OpenGLRegistryParserState.INCLUDED_FEATURE_LIST:
			self.state = OpenGLRegistryParserState.INCLUDED_FEATURE_LIST_REQUIRE

		if name == "command" and self.state == OpenGLRegistryParserState.EXCLUDED_FEATURE_LIST_REQUIRE:
			functionName = attrs['name']

			if (functionName):
				self.exclusionSet.add(functionName)

		if name == "command" and self.state == OpenGLRegistryParserState.INCLUDED_FEATURE_LIST_REQUIRE:
			functionName = attrs['name']

			if (functionName):
				self.inclusionSet.add(functionName)

	def endElement(self, name):
		if name == "registry" and self.state == OpenGLRegistryParserState.ROOT_NODE:
			self.state = OpenGLRegistryParserState.NONE
		if name == "feature" and self.state == OpenGLRegistryParserState.EXCLUDED_FEATURE_LIST:
			self.state = OpenGLRegistryParserState.ROOT_NODE
		if name == "feature" and self.state == OpenGLRegistryParserState.INCLUDED_FEATURE_LIST:
			self.state = OpenGLRegistryParserState.ROOT_NODE
		if name == "require" and self.state == OpenGLRegistryParserState.EXCLUDED_FEATURE_LIST_REQUIRE:
			self.state = OpenGLRegistryParserState.EXCLUDED_FEATURE_LIST		
		if name == "require" and self.state == OpenGLRegistryParserState.INCLUDED_FEATURE_LIST_REQUIRE:
			self.state = OpenGLRegistryParserState.INCLUDED_FEATURE_LIST

class OpenGLRegistry(xml.sax.ContentHandler):
	
	def __init__(self, srcFile, hdrFile, excludedApiCalls, definedApiCalls, aliasedApiCalls):
		self.state = OpenGLRegistryParserState.NONE	
		self.srcFile = srcFile
		self.hdrFile = hdrFile
		self.excludedApiCalls = excludedApiCalls
		self.apiCallChunk = ''
		self.apiAlias = ''
		self.definedApiCalls = definedApiCalls
		self.aliasedApiCalls = aliasedApiCalls

	def startElement(self, name, attrs):
		if name == "registry" and self.state == OpenGLRegistryParserState.NONE:
			self.state = OpenGLRegistryParserState.ROOT_NODE
		if name == "commands" and self.state == OpenGLRegistryParserState.ROOT_NODE: # OpenGL API Call
			self.state = OpenGLRegistryParserState.COMMAND_LIST
		if name == "command" and self.state == OpenGLRegistryParserState.COMMAND_LIST:
			self.state = OpenGLRegistryParserState.COMMAND
		if name == "proto" and self.state == OpenGLRegistryParserState.COMMAND:
			self.state = OpenGLRegistryParserState.PROTO		
		if name == "name" and self.state == OpenGLRegistryParserState.PROTO:
			self.state = OpenGLRegistryParserState.PROTO_NAME		
		if name == "alias" and self.state == OpenGLRegistryParserState.COMMAND:
			self.state = OpenGLRegistryParserState.COMMAND_ALIAS
			self.apiAlias = attrs['name'];		
			
	def characters(self, content):		
		if self.state == OpenGLRegistryParserState.PROTO_NAME:
			self.apiCallChunk = self.apiCallChunk + content			

	def endElement(self, name):
		if name == "registry" and self.state == OpenGLRegistryParserState.ROOT_NODE:
			self.state = OpenGLRegistryParserState.NONE
		if name == "commands" and self.state == OpenGLRegistryParserState.COMMAND_LIST:
			self.state = OpenGLRegistryParserState.ROOT_NODE
		if name == "command" and self.state == OpenGLRegistryParserState.COMMAND:
			trackStaticFunctionBinding(self.srcFile, self.hdrFile, self.excludedApiCalls, self.definedApiCalls, self.aliasedApiCalls, self.apiCallChunk, self.apiAlias)
			self.apiCallChunk = ''
			self.apiAlias = ''
			self.state = OpenGLRegistryParserState.COMMAND_LIST
		if name == "proto" and self.state == OpenGLRegistryParserState.PROTO:
			self.state = OpenGLRegistryParserState.COMMAND		
		if name == "name" and self.state == OpenGLRegistryParserState.PROTO_NAME:			
			self.state = OpenGLRegistryParserState.PROTO		
		if name == "alias" and self.state == OpenGLRegistryParserState.COMMAND_ALIAS:
			self.state = OpenGLRegistryParserState.COMMAND

# This function is used to generate runtime API bindings for OpenGL, in the global namespace.
def genBindings(registryPath, registryFileName, srcFile, hdrFile):

	os.makedirs(os.path.dirname(srcFile), exist_ok=True)
	os.makedirs(os.path.dirname(hdrFile), exist_ok=True)

	srcOutputFile = open(srcFile, "w+")	
	hdrOutputFile = open(hdrFile, "w+")

	registryFilePath = os.path.join(registryPath, registryFileName)
	excludedApiCalls = set()
	includedApiCalls = set()
	definedApiCalls = set()
	aliasedApiCalls = dict()

	print('Building API exclusion list...')
	openGLExlusionsParser = xml.sax.make_parser()
	openGLExlusionsParser.setContentHandler(OpenGLRegistryExclusions(excludedApiCalls, includedApiCalls))
	openGLExlusionsParser.parse(open(registryFilePath, "r"))

	# Some calls defined in other OpenGL profiles, might still be valid, so we preserve them.
	for apiCall in includedApiCalls:
		if apiCall in excludedApiCalls:
			excludedApiCalls.remove(apiCall)

	print('Generating C binding...')
	writeHdrFilePrefix(hdrOutputFile)
	writeSrcFilePrefix(srcOutputFile)

	xmlParser = xml.sax.make_parser()
	xmlParser.setContentHandler(OpenGLRegistry(srcOutputFile, hdrOutputFile, excludedApiCalls, definedApiCalls, aliasedApiCalls))			
	xmlParser.parse(open(registryFilePath, "r"))

	writeBindingImplementation(srcOutputFile, definedApiCalls, aliasedApiCalls)

	writeHdrFileSuffix(hdrOutputFile)
	writeSrcFileSuffix(srcOutputFile)

	print('Done!')

if __name__ == '__main__':
	
	argParser = argparse.ArgumentParser(description='Generate OpenGL runtime Bindings from OpenGL Registry')
	argParser.add_argument('--xmlDir', help='The path to the OpenGL-Registry XML directory')
	argParser.add_argument('--xmlName', help='override registry input file', default='gl.xml')
	argParser.add_argument('--srcFile', help='override C output file path', default='../src/opengl.c')
	argParser.add_argument('--hdrFile', help='override output header file path')
	argParser.add_argument('--extensionDir', help='override extension registry directory')
	args = argParser.parse_args()

	print('Finding OpenGL extension suffixies...')
	findNonPortableExtensionSuffixes(args.extensionDir)	

	genBindings(args.xmlDir, args.xmlName, args.srcFile, args.hdrFile)		