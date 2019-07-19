import os, argparse
import xml.etree.ElementTree as ET

class OpenGLParam():
	def __init__(self, name, type):
		self.name = name
		self.type = type

class OpenGLCommand():
	def __init__(self, namespace, prototype, name, params):
		self.prototype = prototype
		self.name = name
		self.params = params

class OpenGLProfile():
	def __init__(self, profile, name, commands):
		self.profile = profile
		self.name = name
		self.commands = commands

def loadRegistry(xmlPath):
	tree = ET.parse(xmlPath)
	root = tree.getroot()
	return root

def getCommands(registry):

	commandsDict = dict()

	for commands in registry:
		if commands.tag != 'commands':
			continue

		namespace = commands.get('namespace', default='')		

		for command in commands:			
			if (command.tag != 'command'):
				continue		

			cmdPrototype = ''
			cmdName = ''
			cmdParams = list()

			for commandDetail in command:				
				if commandDetail.tag == 'proto':
					cmdPrototype = commandDetail.text or ''

					for name in commandDetail:
						if (name.tag != 'name'):
							continue
						
						cmdName = name.text

				if commandDetail.tag == 'param':
					paramType = ''
					paramName = ''

					for tag in commandDetail:
						if tag == 'ptype':
							paramType = tag.text
						if tag == 'name':
							paramName = tag.text

					cmdParams.insert(0, OpenGLParam(paramName, paramType))
			
			commandsDict[cmdName] = (OpenGLCommand(namespace, cmdPrototype, cmdName, cmdParams))

	return commandsDict

def createProfiles(registry):
	profileList = list()

	commands = getCommands(registry)

	for feature in registry:
		if feature.tag != 'feature':
			continue

		profile = feature.get('api', default='')
		name = feature.get('name', default='')

		for require in feature:
			if require.tag != 'require':
				continue

			profileCommands = list()
			
			for command in require:
				if command.tag != 'command':
					continue

				commandName = command.get('name', default='')				
				profileCommands.insert(0, commands[commandName])

		profileList.append(OpenGLProfile(profile, name, profileCommands))

	return profileList

def writeHeaderFile(profiles, hdrFileName):	
	if not os.path.exists(os.path.dirname(hdrFileName)):
		os.makedirs(os.path.dirname(hdrFileName), exist_ok=True)

	hdrFile = open(hdrFileName, "w+")

	hdrFile.write("""#pragma once

#include <gweekgl/platform.h>

#ifdef __cplusplus
extern "C" 
{
#endif

\t/* Needed to trigger binding initialization from the system OpenGL libraries. */
\tvoid gweekgl_initialize();
	
""")

	for profile in profiles:
		hdrFile.write(f"#ifdef {profile.name}\n")		

		for command in profile.commands:
			hdrFile.write(f"\tPFN{command.name.upper()}PROC {command.name};\n")

		hdrFile.write(f"#endif /* {profile.name} */\n")

	hdrFile.write("""
#ifdef __cplusplus
}
#endif
""")

def writeSourceFile(profiles, sourceFileName):
	if not os.path.exists(os.path.dirname(sourceFileName)):
		os.makedirs(os.path.dirname(sourceFileName), exist_ok=True)

	sourceFile = open(sourceFileName, "w+")

	sourceFile.write("""#include <gweekgl/opengl.h>

""")

	for profile in profiles:
		sourceFile.write(f'#ifdef {profile.name}\n')		

		for command in profile.commands:
			sourceFile.write(f'PFN{command.name.upper()}PROC {command.name};\n')

		sourceFile.write(f'#endif /* {profile.name} */\n')

	sourceFile.write("""
void gweekgl_initialize()
{
""")

	for profile in profiles:
		sourceFile.write(f"#ifdef {profile.name}\n")

		for command in profile.commands:
			sourceFile.write(f'\t{command.name} = (PFN{command.name.upper()}PROC)(GWEEK_PROC_ADDR_FUNC("{command.name}");\n')

		sourceFile.write(f"#endif /* {profile.name} */\n")

	sourceFile.write("}")

if __name__ == '__main__':

	argParser = argparse.ArgumentParser(description='Generate OpenGL runtime Bindings from OpenGL Registry')
	argParser.add_argument('--xmlDir', help='The path to the OpenGL-Registry XML directory')
	argParser.add_argument('--xmlName', help='override registry input file', default='gl.xml')
	argParser.add_argument('--srcFile', help='override C output file path', default='../src/opengl.c')
	argParser.add_argument('--hdrFile', help='override output header file path')
	argParser.add_argument('--extensionDir', help='override extension registry directory')
	args = argParser.parse_args()

	print(f"Loading OpenGL Registry from: '{args.xmlName}''")
	registry = loadRegistry(os.path.join(args.xmlDir, args.xmlName))
	profiles = createProfiles(registry)
	
	writeHeaderFile(profiles, args.hdrFile)
	writeSourceFile(profiles, args.srcFile)