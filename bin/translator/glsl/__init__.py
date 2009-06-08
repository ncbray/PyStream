from . shadertranslator import GLSLTranslator
from language.glsl import codegen

from . pythonshader import PythonShader

from abstractcode.shaderprogram import ShaderProgram

class CompilerContext(object):
	def __init__(self, console, extractor, interface):
		self.console   = console
		self.extractor = extractor
		self.interface = interface




def makePathMatcher(interface):
	root = {}
	for path, name, input, output in interface.glsl.attr:
		current = root
		for part in reversed(path[1:]):
			if part not in current:
				current[part] = {}
			current = current[part]

		current[path[0]] = name

	return root

def translate(console, dataflow, interface):
	context = CompilerContext(console, dataflow.extractor, interface)

	with context.console.scope('translate to glsl'):
		pathMatcher = makePathMatcher(context.interface)

		translator = GLSLTranslator(intrinsics.makeIntrinsicRewriter(context.extractor))

		# HACK should only target shader?
		for code in context.interface.entryCode():
			if isinstance(code, ShaderProgram):

				shadercode = code.vertexShaderCode()
				shader = PythonShader(shadercode, pathMatcher)
				iotransform.evaluateShader(context, shader, pathMatcher)
				result = translator.processShader(shader)

				print str(shadercode)
				print
				print codegen.GLSLCodeGen()(result)
				print
				print


				shadercode = code.fragmentShaderCode()
				shader = PythonShader(shadercode, pathMatcher)
				iotransform.evaluateShader(context, shader, pathMatcher)
				result = translator.processShader(shader)

				print str(shadercode)
				print
				print codegen.GLSLCodeGen()(result)
				print
				print