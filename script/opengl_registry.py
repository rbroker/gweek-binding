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

class OpenGLCommandRemoval():
	def __init__(self, name, feature):
		self.name = name		
		self.feature = feature

class OpenGLFeature():
	def __init__(self, api, name, requiredCommands, removedCommands):
		self.api = api
		self.name = name
		self.requiredCommands = requiredCommands
		self.removedCommands = removedCommands		

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

					cmdParams.append(OpenGLParam(paramName, paramType))
			
			commandsDict[cmdName] = OpenGLCommand(namespace, cmdPrototype, cmdName, cmdParams)

	return commandsDict

def getExtensionMethods(registry):
	extensionSet = dict()

	for extensions in registry:
		if extensions.tag != 'extensions':
			continue

		for extension in extensions:			

			name = extension.get('name', default='')

			for require in extension:
				if require.tag != 'require':
					continue

				for command in require:
					if command.tag != 'command':
						continue
					
					commandName = command.get('name', default='')					
					extensionSet[commandName] = name

	return extensionSet
		

def createFeatureSet(registry):
	featureSet = list()

	commands = getCommands(registry)

	for feature in registry:
		if feature.tag != 'feature':
			continue		

		api = feature.get('api', default='')
		name = feature.get('name', default='')
		requiredCommands = dict()
		removedCommands = dict()		

		# Skip generation of bindings for OpenGL Versions < 1.1
		# as these should already be fully defined & exported.
		if api == 'gl' and float(feature.get('number', default=0)) <= 1.1:
			continue

		for featureDefinition in feature:			
			if featureDefinition.tag == 'require':		
				for command in featureDefinition:
					if command.tag != 'command':
						continue
					
					commandName = command.get('name', default='')													
					requiredCommands[commandName] = commands[commandName]
			
			if featureDefinition.tag == 'remove':
				for command in featureDefinition:
					if command.tag != 'command':
						continue

					commandName = command.get('name', default='')									
					removedCommands[commandName] = commands[commandName]

		featureSet.append(OpenGLFeature(api, name, requiredCommands, removedCommands))

	return featureSet

def generatedRemovedCommandState(featureSets):
	removedCommands = dict()
	for feature in featureSets:
		for command in feature.removedCommands:
			removedCommands[command] = OpenGLCommandRemoval(command, feature.name)	

	return removedCommands

def writeHeaderFile(featureSets, removedCommands, extensionMethods, hdrFileName):	
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

	for feature in featureSets:
		hdrFile.write(f"#ifdef {feature.name}\n")
		hdrFile.write(f"#ifndef GWEEK_SYSTEM_DEFINES_{feature.name}\n")

		for command in feature.requiredCommands:			
			if command in removedCommands:
				hdrFile.write(f"""#ifndef {removedCommands[command].feature} /* Removed In {removedCommands[command].feature} */
\textern PFN{command.upper()}PROC {command};
#endif
""")
			elif command in extensionMethods:
				hdrFile.write(f"""#ifndef GWEEK_SYSTEM_DEFINES_{extensionMethods[command]} /* Added by an extension */
\textern PFN{command.upper()}PROC {command};
#endif
""")
			else:
				hdrFile.write(f"\textern PFN{command.upper()}PROC {command};\n")

		hdrFile.write(f"#endif /* GWEEK_SYSTEM_DEFINES_{feature.name} */\n")
		hdrFile.write(f"#endif /* {feature.name} */\n")

	hdrFile.write("""
#ifdef __cplusplus
}
#endif
""")

def writeSourceFile(featureSets, removedCommands, extensionMethods, sourceFileName):
	if not os.path.exists(os.path.dirname(sourceFileName)):
		os.makedirs(os.path.dirname(sourceFileName), exist_ok=True)

	sourceFile = open(sourceFileName, "w+")

	sourceFile.write("""#include <gweekgl/opengl.h>

""")

	for feature in featureSets:
		sourceFile.write(f'#ifdef {feature.name}\n')		
		sourceFile.write(f"#ifndef GWEEK_SYSTEM_DEFINES_{feature.name}\n")

		for command in feature.requiredCommands:
			if command in removedCommands:
				sourceFile.write(f"""#ifndef {removedCommands[command].feature} /* Removed In {removedCommands[command].feature} */
PFN{command.upper()}PROC {command};
#endif
""")
			elif command in extensionMethods:
				sourceFile.write(f"""#ifndef GWEEK_SYSTEM_DEFINES_{extensionMethods[command]} /* Added by an extension */
PFN{command.upper()}PROC {command};
#endif
""")
			else:
				sourceFile.write(f'PFN{command.upper()}PROC {command};\n')
	
		sourceFile.write(f'#endif /* GWEEK_SYSTEM_DEFINES_{feature.name} */\n')
		sourceFile.write(f'#endif /* {feature.name} */\n')

	sourceFile.write("""
void gweekgl_initialize()
{
""")

	for feature in featureSets:
		sourceFile.write(f"#ifdef {feature.name}\n")
		sourceFile.write(f"#ifndef GWEEK_SYSTEM_DEFINES_{feature.name}\n")

		for command in feature.requiredCommands:
			if command in removedCommands:			
				sourceFile.write(f"""#ifndef {removedCommands[command].feature} /* Removed In {removedCommands[command].feature} */
\t{command} = (PFN{command.upper()}PROC)GWEEK_PROC_ADDR_FUNC("{command}");
#endif
""")
			elif command in extensionMethods:
				sourceFile.write(f"""#ifndef GWEEK_SYSTEM_DEFINES_{extensionMethods[command]} /* Added by an extension */
\t{command} = (PFN{command.upper()}PROC)GWEEK_PROC_ADDR_FUNC("{command}");
#endif
""")
			else:
				sourceFile.write(f'\t{command} = (PFN{command.upper()}PROC)GWEEK_PROC_ADDR_FUNC("{command}");\n')

		sourceFile.write(f"#endif /* GWEEK_SYSTEM_DEFINES_{feature.name} */\n")
		sourceFile.write(f"#endif /* {feature.name} */\n")

	sourceFile.write("}")

if __name__ == '__main__':

	argParser = argparse.ArgumentParser(description='Generate OpenGL runtime Bindings from OpenGL Registry')
	argParser.add_argument('--xmlDir', help='The path to the OpenGL-Registry XML directory')
	argParser.add_argument('--xmlName', help='override registry input file', default='gl.xml')
	argParser.add_argument('--srcFile', help='override C output file path', default='../src/opengl.c')
	argParser.add_argument('--hdrFile', help='override output header file path')	
	args = argParser.parse_args()

	print(f"Loading OpenGL Registry from: '{args.xmlName}''")
	registry = loadRegistry(os.path.join(args.xmlDir, args.xmlName))
	featureSets = createFeatureSet(registry)
	extensionMethods = getExtensionMethods(registry)	
	removedCommands = generatedRemovedCommandState(featureSets)

	writeHeaderFile(featureSets, removedCommands, extensionMethods, args.hdrFile)
	writeSourceFile(featureSets, removedCommands, extensionMethods, args.srcFile)