# This script generates a set of runtime OpenGL bindings for API extensions.

nonPortableExtensions = set()

import sys, os, argparse, xml.sax

from enum import Enum

def findNonPortableExtensionSuffixes(extensionDir):
	# https://www.opengl.org/archives/resources/features/OGLextensions/	
	print(extensionDir)
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

def writeCppFilePrefix(cppFile):
	cppFile.write('#include "platform.h"\n')
#	cppFile.write('#include <GL/glcorearb.h>\n')
	cppFile.write('#include <GL/glext.h>\n')
#	cppFile.write('#include <GL/glxext.h>\n')
#	cppFile.write('#include <GL/wgl.h>\n')
#	cppFile.write('#include <GL/wglext.h>\n')
	cppFile.write('\n')
	cppFile.write('namespace\n')
	cppFile.write('{\n')

def writeCppFileSuffix(cppFile):
	cppFile.write('}\n')

def writeStaticFunctionBinding(cppFile, excludedApiCalls, definedApiCalls, name, alias):

	for extensionSuffix in nonPortableExtensions:
		if name.endswith(extensionSuffix):
			return

	if name in excludedApiCalls:
		return	

	if name == 'glGetPointerv':
		return # HACK, not sure why the default Chronos headers don't generate this function ptr.

	definedApiCalls.add(name)
	
	if not alias or alias not in definedApiCalls:
		cppFile.write('\tstatic const auto ' + name + ' = reinterpret_cast<PFN' + name.upper() + 'PROC>(GWEEK_PROC_ADDR_FUNC("' + name + '"));\n')
	else:
		cppFile.write('\tstatic const auto ' + name + ' = reinterpret_cast<PFN' + name.upper() + 'PROC>(' + alias + ');\n')

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
	
	def __init__(self, cppFile, excludedApiCalls):
		self.state = OpenGLRegistryParserState.NONE	
		self.cppFile = cppFile
		self.excludedApiCalls = excludedApiCalls
		self.apiCallChunk = ''
		self.apiAlias = ''
		self.definedApiCalls = set()

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
			writeStaticFunctionBinding(self.cppFile, self.excludedApiCalls, self.definedApiCalls, self.apiCallChunk, self.apiAlias)
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
def genBindings(registryPath, registryFileName, cppFile):

	os.makedirs(os.path.dirname(cppFile), exist_ok=True)

	cppOutputFile = open(cppFile, "w+")	

	registryFilePath = os.path.join(registryPath, registryFileName)
	excludedApiCalls = set()
	includedApiCalls = set()

	print('Building API exclusion list...')
	openGLExlusionsParser = xml.sax.make_parser()
	openGLExlusionsParser.setContentHandler(OpenGLRegistryExclusions(excludedApiCalls, includedApiCalls))
	openGLExlusionsParser.parse(open(registryFilePath, "r"))

	# Some calls defined in other OpenGL profiles, might still be valid, so we preserve them.
	for apiCall in includedApiCalls:
		if apiCall in excludedApiCalls:
			excludedApiCalls.remove(apiCall)

	print('Generating C++ binding...')
	writeCppFilePrefix(cppOutputFile)

	xmlParser = xml.sax.make_parser()
	xmlParser.setContentHandler(OpenGLRegistry(cppOutputFile, excludedApiCalls))			
	xmlParser.parse(open(registryFilePath, "r"))

	writeCppFileSuffix(cppOutputFile)

	print('Done!')

if __name__ == '__main__':
	
	argParser = argparse.ArgumentParser(description='Generate OpenGL runtime Bindings from OpenGL Registry')
	argParser.add_argument('--xmlDir', help='The path to the OpenGL-Registry XML directory')
	argParser.add_argument('--xmlName', help='override registry input file', default='gl.xml')
	argParser.add_argument('--cppFile', help='override C++ output file path', default='../src/gl.cpp')
	argParser.add_argument('--extensionDir', help='override extension registry directory')
	args = argParser.parse_args()

	print('Finding OpenGL extension suffixies...')
	findNonPortableExtensionSuffixes(args.extensionDir)	

	genBindings(args.xmlDir, args.xmlName, args.cppFile)		