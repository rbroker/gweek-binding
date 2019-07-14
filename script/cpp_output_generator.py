from reg import *

# COutputBindingGenerator - subclass of OutputGenerator.
# Generates C-language API interfaces.
#
# ---- methods ----
# COutputBindingGenerator(errFile, warnFile, diagFile) - args as for
#   COutputBindingGenerator. Defines additional internal state.
# makeCDecls(cmd) - return C prototype and function pointer typedef for a
#     <command> Element, as a list of two strings
#   cmd - Element for the <command>
# newline() - print a newline to the output file (utility function)
# ---- methods overriding base class ----
# beginFile(genOpts)
# endFile()
# beginFeature(interface, emit)
# endFeature()
# genType(typeinfo,name) - generate interface for a type
# genEnum(enuminfo, name)
# genCmd(cmdinfo)
class COutputBindingGenerator(OutputGenerator):
    """Generate specified API interfaces in a specific style, such as a C header"""
    def __init__(self,
                 errFile = sys.stderr,
                 warnFile = sys.stderr,
                 diagFile = sys.stdout):
        OutputGenerator.__init__(self, errFile, warnFile, diagFile)
        # Internal state - accumulators for different inner block text
        self.typeBody = ''
        self.enumBody = ''
        self.cmdBody = ''
    #
    # makeCDecls - return C prototype and function pointer typedef for a
    #   command, as a two-element list of strings.
    # cmd - Element containing a <command> tag
    def makeCDecls(self, cmd):
        """Generate C function pointer typedef for <command> Element"""
        proto = cmd.find('proto')
        params = cmd.findall('param')
        # Begin accumulating prototype and typedef strings
        pdecl = self.genOpts.apicall
        tdecl = 'typedef '
        #
        # Insert the function return type/name.
        # For prototypes, add APIENTRY macro before the name
        # For typedefs, add (APIENTRYP <name>) around the name and
        #   use the PFNGLCMDNAMEPROC nameng convention.
        # Done by walking the tree for <proto> element by element.
        # lxml.etree has elem.text followed by (elem[i], elem[i].tail)
        #   for each child element and any following text
        # Leading text
        pdecl += noneStr(proto.text)
        tdecl += noneStr(proto.text)
        # For each child element, if it's a <name> wrap in appropriate
        # declaration. Otherwise append its contents and tail contents.
        for elem in proto:
            text = noneStr(elem.text)
            tail = noneStr(elem.tail)
            if (elem.tag == 'name'):
                pdecl += self.genOpts.apientry + text + tail
                tdecl += '(' + self.genOpts.apientryp + 'PFN' + text.upper() + 'PROC' + tail + ')'
            else:
                pdecl += text + tail
                tdecl += text + tail
        # Now add the parameter declaration list, which is identical
        # for prototypes and typedefs. Concatenate all the text from
        # a <param> node without the tags. No tree walking required
        # since all tags are ignored.
        n = len(params)
        paramdecl = ' ('
        if n > 0:
            for i in range(0,n):
                paramdecl += ''.join([t for t in params[i].itertext()])
                if (i < n - 1):
                    paramdecl += ', '
        else:
            paramdecl += 'void'
        paramdecl += ');\n';
        return [ pdecl + paramdecl, tdecl + paramdecl ]
    #
    def newline(self):
        write('', file=self.outFile)
    #
    def beginFile(self, genOpts):
        OutputGenerator.beginFile(self, genOpts)
        # C-specific
        #
        # Multiple inclusion protection & C++ wrappers.
        if (genOpts.protectFile and self.genOpts.filename):
            headerSym = '__' + self.genOpts.apiname + '_' + re.sub('\.h', '_h_', os.path.basename(self.genOpts.filename))
            write('#ifndef', headerSym, file=self.outFile)
            write('#define', headerSym, '1', file=self.outFile)
            self.newline()
        write('#ifdef __cplusplus', file=self.outFile)
        write('extern "C" {', file=self.outFile)
        write('#endif', file=self.outFile)
        self.newline()
        #
        # User-supplied prefix text, if any (list of strings)
        if (genOpts.prefixText):
            for s in genOpts.prefixText:
                write(s, file=self.outFile)
        #
        # Some boilerplate describing what was generated - this
        # will probably be removed later since the extensions
        # pattern may be very long.
        write('/* Generated C header for:', file=self.outFile)
        write(' * API:', genOpts.apiname, file=self.outFile)
        if (genOpts.profile):
            write(' * Profile:', genOpts.profile, file=self.outFile)
        write(' * Versions considered:', genOpts.versions, file=self.outFile)
        write(' * Versions emitted:', genOpts.emitversions, file=self.outFile)
        write(' * Default extensions included:', genOpts.defaultExtensions, file=self.outFile)
        write(' * Additional extensions included:', genOpts.addExtensions, file=self.outFile)
        write(' * Extensions removed:', genOpts.removeExtensions, file=self.outFile)
        write(' */', file=self.outFile)
    def endFile(self):
        # C-specific
        # Finish C++ wrapper and multiple inclusion protection
        self.newline()
        write('#ifdef __cplusplus', file=self.outFile)
        write('}', file=self.outFile)
        write('#endif', file=self.outFile)
        if (self.genOpts.protectFile and self.genOpts.filename):
            self.newline()
            write('#endif', file=self.outFile)
        # Finish processing in superclass
        OutputGenerator.endFile(self)
    def beginFeature(self, interface, emit):
        # Start processing in superclass
        OutputGenerator.beginFeature(self, interface, emit)
        # C-specific
        # Accumulate types, enums, function pointer typedefs, end function
        # prototypes separately for this feature. They're only printed in
        # endFeature().
        self.typeBody = ''
        self.enumBody = ''
        self.cmdPointerBody = ''
        self.cmdBody = ''
    def endFeature(self):
        # C-specific
        # Actually write the interface to the output file.
        if (self.emit):
            self.newline()
            if (self.genOpts.protectFeature):
                write('#ifndef', self.featureName, file=self.outFile)
            write('#define', self.featureName, '1', file=self.outFile)
            if (self.typeBody != ''):
                write(self.typeBody, end='', file=self.outFile)
            #
            # Don't add additional protection for derived type declarations,
            # which may be needed by other features later on.
            if (self.featureExtraProtect != None):
                write('#ifdef', self.featureExtraProtect, file=self.outFile)
            if (self.enumBody != ''):
                write(self.enumBody, end='', file=self.outFile)
            if (self.genOpts.genFuncPointers and self.cmdPointerBody != ''):
                write(self.cmdPointerBody, end='', file=self.outFile)
            if (self.cmdBody != ''):
                if (self.genOpts.protectProto == True):
                    prefix = '#ifdef ' + self.genOpts.protectProtoStr + '\n'
                    suffix = '#endif\n'
                elif (self.genOpts.protectProto == 'nonzero'):
                    prefix = '#if ' + self.genOpts.protectProtoStr + '\n'
                    suffix = '#endif\n'
                elif (self.genOpts.protectProto == False):
                    prefix = ''
                    suffix = ''
                else:
                    self.gen.logMsg('warn',
                                    '*** Unrecognized value for protectProto:',
                                    self.genOpts.protectProto,
                                    'not generating prototype wrappers')
                    prefix = ''
                    suffix = ''

                write(prefix + self.cmdBody + suffix, end='', file=self.outFile)
            if (self.featureExtraProtect != None):
                write('#endif /*', self.featureExtraProtect, '*/', file=self.outFile)
            if (self.genOpts.protectFeature):
                write('#endif /*', self.featureName, '*/', file=self.outFile)
        # Finish processing in superclass
        OutputGenerator.endFeature(self)
    #
    # Type generation
    def genType(self, typeinfo, name):
        OutputGenerator.genType(self, typeinfo, name)
        #
        # Replace <apientry /> tags with an APIENTRY-style string
        # (from self.genOpts). Copy other text through unchanged.
        # If the resulting text is an empty string, don't emit it.
        typeElem = typeinfo.elem
        s = noneStr(typeElem.text)
        for elem in typeElem:
            if (elem.tag == 'apientry'):
                s += self.genOpts.apientry + noneStr(elem.tail)
            else:
                s += noneStr(elem.text) + noneStr(elem.tail)
        if (len(s) > 0):
            self.typeBody += s + '\n'
    #
    # Enumerant generation
    def genEnum(self, enuminfo, name):
        OutputGenerator.genEnum(self, enuminfo, name)
        #
        # EnumInfo.type is a C value suffix (e.g. u, ull)
        self.enumBody += '#define ' + name.ljust(33) + ' ' + enuminfo.elem.get('value')
        #
        # Handle non-integer 'type' fields by using it as the C value suffix
        t = enuminfo.elem.get('type')
        if (t != '' and t != 'i'):
            self.enumBody += enuminfo.type
        self.enumBody += '\n'
    #
    # Command generation
    def genCmd(self, cmdinfo, name):
        OutputGenerator.genCmd(self, cmdinfo, name)
        #
        decls = self.makeCDecls(cmdinfo.elem)
        self.cmdBody += decls[0]
        if (self.genOpts.genFuncPointers):
            self.cmdPointerBody += decls[1]