import viz
import vizmat
import os

###############################################
################ Constants ####################
###############################################

CAUSTIC_SCALE = 0.2
CAUSTIC_INTENSITY = 1.0

#Maximum number of texture coordinate units supported by card
MAX_TEXCOORD_UNITS = 8

#Maximum number of texture units supported by card
MAX_TEX_UNITS = 16

#Maximum number of allowable blend units by current implementation
MAX_BLEND_UNITS	= 4

DIFFUSE_MAP		= ['Co','C2','C3','C4']
NORMAL_MAP		= ['No','N2','N3','N4']
PARALLAX_MAP	= ['Pa','P2','P3','P4']
LIGHT_MAP		= ['Li','L2','L3','L4']
SPECULAR_MAP	= ['Sp','S2','S3','S4']
DETAIL_MAP		= ['De','D2','D3','D4']
SPHERE_MAP		= ['Re','R2','R3','R4']
ENV_MAP			= ['En','E2','E3','E4']
BLEND_MAP		= 'Ma'
MATERIAL_IDS	= DIFFUSE_MAP + NORMAL_MAP + PARALLAX_MAP + LIGHT_MAP + SPECULAR_MAP + DETAIL_MAP + SPHERE_MAP + ENV_MAP + [BLEND_MAP]

#Models that use vertex animation will have the following flag in their name
ANIMATE_FLAG	= '[ANIM]'

#Name of node to apply water refraction to
REFRACT_NODE	= 'water'

#Logs shaders to a file
LOG_SHADERS = False

###############################################
################ Global Uniforms ##############
###############################################

#Uniform used by all vertex shaders to get active light
_lightUniform = viz.addUniformInt('light',0)

#Uniform for controlling lightmap intensity
_lightMapUniform = viz.addUniformFloat('lightmap_scale',1.0)

#Uniform used by all fragment shaders to control ambient light
_ambientUniform = viz.addUniformFloat('ambient',0.0)

#Uniform for specifying global fog density
_fogUniform = viz.addUniformFloat('fog',0.0)

#Uniform for specifying caustics
_causticUniform = viz.addUniformFloat('caustic',0)
_causticScaleUniform = viz.addUniformFloat('causticScale',CAUSTIC_SCALE)
_causticTexture = None

#Uniforms for enabling/disabling vertex animation
_animationOnUniform = viz.addUniformBool('animate',True)
_animationOffUniform = viz.addUniformBool('animate',False)

#Uniforms for enabling/disabling refraction depth
_refractDepthOnUniform = viz.addUniformBool('refractDepth',True)
_refractDepthOffUniform = viz.addUniformBool('refractDepth',False)

#Uniforms for parallax map scale/bias
_parallaxScaleUniform = viz.addUniformFloat('parallaxScale',float(viz.getOption('vizshader.parallax.scale','0.08')))
_parallaxBiasUniform = viz.addUniformFloat('parallaxBias',float(viz.getOption('vizshader.parallax.bias','0.04')))

#List of uniforms representing each texture unit
_texUniform = [viz.addUniformInt('tex'+str(i),i) for i in xrange(MAX_TEX_UNITS)]

#List of global uniforms that are applied to all shaders
_globalUniforms = [	_lightUniform
					,_lightMapUniform
					,_ambientUniform
					,_fogUniform
					,_causticUniform
					,_causticScaleUniform
					,_refractDepthOffUniform
					,_animationOffUniform
					,_parallaxScaleUniform
					,_parallaxBiasUniform
					]

###############################################
############## Private functions ##############
###############################################

#Shader cache that maps a material string to a shader object
_shaderCache = {}

def texCoord(unit):
	"""Create texture coord"""
	index = unit / 2
	swizzle = ['xy','zw'][unit%2]
	return 'gl_TexCoord['+str(index)+'].'+swizzle

def texCoordCopy(unit):
	"""Create code for a vertex shader to copy the texture coordinates"""
	index = unit / 2
	swizzle = ['xy','zw'][unit%2]
	if unit >= MAX_TEXCOORD_UNITS:
		return 'gl_TexCoord['+str(index)+'].'+swizzle+' = gl_MultiTexCoord'+str(unit-MAX_TEXCOORD_UNITS)+'.zw;\n'
	return 'gl_TexCoord['+str(index)+'].'+swizzle+' = gl_MultiTexCoord'+str(unit)+'.xy;\n'

def texture(unit,coordUnit=None,coordOffset=''):
	"""Create texture lookup code for a fragment shader on the specified texture unit"""
	if coordUnit is None:
		coordUnit = unit
	index = coordUnit / 2
	swizzle = ['xy','zw'][coordUnit%2]
	return 'texture2D('+_texUniform[unit].getName()+',gl_TexCoord['+str(index)+'].'+swizzle+coordOffset+')'

def textureWithCoord(unit,coordCode,cubeMap=False):
	"""Create texture lookup code given GLSL code for the texture coordinates to use"""
	if cubeMap:
		return 'textureCube('+_texUniform[unit].getName()+','+coordCode+')'
	return 'texture2D('+_texUniform[unit].getName()+','+coordCode+')'

def _getShader(material,name):

	#See if material is already cached
	if material in _shaderCache:
		return _shaderCache[material]

	#Generate the unit map
	units = {}
	for i in xrange(len(material)/2):
		id = material[i*2:i*2+2]
		if id in MATERIAL_IDS:
			units[id] = i
		else:
			viz.logWarn('** WARNING: Encountered invalid material ID \'',id,'\' in \'',name,'\'')
	
	#List of units being used
	texUnits = []
	
	#Maps texture unit to texture type string
	texUnitType = {}
	
	#Coordinate for generating tangent data
	normalMapUnit = 0
	
	#Retrieve blend map unit
	blendUnit = units.get(BLEND_MAP)
	
	#Caustic unit is last available texture unit
	causticUnit = len(units)
	texUnits.append(causticUnit)
	
	vert = """
	varying vec3 lightVec;
	varying vec3 eyeVec;
	attribute vec3 Tangent;
	uniform int light;
	uniform bool animate;
	uniform bool refractDepth;
	uniform float caustic;
	uniform float causticScale;
	uniform float osg_FrameTime;
	uniform mat4 osg_ViewMatrixInverse;
	
	#define SURFACE_GAIN	0.01
	#define MOTION_GAIN		10.0
	#define WATER_HEIGHT	0.5
	
	void main(void)
	{
		vec4 glVertex = gl_Vertex;
		if(animate) {
			vec4 world = osg_ViewMatrixInverse * gl_ModelViewMatrix * glVertex;
			float theta = SURFACE_GAIN * (abs(world.x)+abs(world.z)) + osg_FrameTime*3.28;
			float gain = gl_Color.r * MOTION_GAIN;
			
			glVertex.x += gain * cos(theta / 5.0);
			glVertex.z += gain * sin(theta / 5.0);
			
			glVertex.x += gain * cos(theta / 17.0);
			glVertex.z += gain * sin(theta / 17.0);
			
			glVertex.x += gain * cos(theta / 37.0);
			glVertex.z += gain * sin(theta / 37.0);
		}
		
		gl_Position = ftransform();
		gl_ClipVertex = gl_ModelViewMatrix * glVertex;
		gl_FogFragCoord = abs(gl_ClipVertex.z);
		
		%copyTexCoords%
		
		if(caustic != 0.0) {
			//Caustic texcoord derived from world xz vertex coordinate
			vec4 worldVertex = osg_ViewMatrixInverse * gl_ClipVertex;
			%causticCoord% = causticScale * worldVertex.xz;
		}
		
		if(refractDepth) {
			vec4 worldVertex = osg_ViewMatrixInverse * gl_ClipVertex;
			gl_FrontColor.a = clamp((WATER_HEIGHT - worldVertex.y) / 2.0,0.0,1.0);
		}
		
		vec3 n = normalize(gl_NormalMatrix * gl_Normal);
		vec3 t = normalize(gl_NormalMatrix * Tangent);
		vec3 b = cross(n, t);
		
		vec3 tmpVec;
		if(gl_LightSource[light].position.w == 0.0) {
			tmpVec = gl_LightSource[light].position.xyz;
		} else {
			tmpVec = vec3(gl_LightSource[light].position-gl_ClipVertex);
		}
		lightVec.x = dot(tmpVec, t);
		lightVec.y = dot(tmpVec, b);
		lightVec.z = dot(tmpVec, n);
		
		tmpVec = -vec3(gl_ClipVertex);
		eyeVec.x = dot(tmpVec, t);
		eyeVec.y = dot(tmpVec, b);
		eyeVec.z = dot(tmpVec, n);
	}
	"""
	
	if blendUnit is None:
	
		#Retrieve material units from map
		diffuseUnit = units.get(DIFFUSE_MAP[0])
		normalUnit = units.get(NORMAL_MAP[0])
		parallaxUnit = units.get(PARALLAX_MAP[0])
		lightUnit = units.get(LIGHT_MAP[0])
		specularUnit = units.get(SPECULAR_MAP[0])
		detailUnit = units.get(DETAIL_MAP[0])
		sphereUnit = units.get(SPHERE_MAP[0])
		envUnit = units.get(ENV_MAP[0])
		
		#Make sure we have a diffuse map
		if diffuseUnit is None:
			viz.logError('** ERROR: Material requires a diffuse map: ',material)
			return None
		
		#If parallax map is defined, then use it as normal map as well
		if parallaxUnit is not None:
			normalUnit = parallaxUnit
		
		frag = """
		varying vec3 lightVec;
		varying vec3 eyeVec;
		uniform bool refractDepth;
		uniform float ambient;
		uniform float lightmap_scale;
		uniform float fog;
		uniform float caustic;
		uniform float parallaxScale;
		uniform float parallaxBias;
		
		%texSamplers%
		
		void main (void)
		{	
			float shininess = 30.0;
			vec3 lVec = normalize(lightVec);
			
			%normalizeEyeVec%
			
			%computeParallax%
			
			%computeNormal%
			float diffuse = 1.0;
			
			
			vec4 diffuseTex = %computeDiffuse%;
			float alpha = diffuseTex.a;
			
			%computeLight%
			%computeSpecular%
			%computeReflection%
			%computeEnvmap%
			
			vec4 baseTex = diffuseTex %lightTex% %detailTex%;
			
			gl_FragColor = (diffuse * baseTex) + (ambient * baseTex) %addSpecular%;
			
			if(caustic != 0.0) {
				gl_FragColor = gl_FragColor + (%causticTex% * diffuse * caustic %causticLight%);
			}
			
			gl_FragColor.a = alpha;
			
			if(fog != 0.0) {
				float f = exp2(fog * gl_FogFragCoord);
				f = clamp(f, 0.0, 1.0);
				gl_FragColor = mix(gl_Fog.color, gl_FragColor, f);
				if(alpha == 0.0) {
					gl_FragColor.a = alpha;
				}
			}
			
			if(refractDepth) {
				gl_FragColor.a = gl_Color.a;
			}
		}
		"""
		
		#Compute parallax offset if necessary
		if parallaxUnit is not None:
			frag = frag.replace('%computeParallax%','vec2 parallaxOffset = ('+texture(parallaxUnit)+'.a * parallaxScale - parallaxBias) * eVec.xy;')
			texOffset = '+parallaxOffset'
		else:
			frag = frag.replace('%computeParallax%','')
			texOffset = ''

		#Generate code for diffuse map
		frag = frag.replace('%computeDiffuse%',texture(diffuseUnit,coordOffset=texOffset))
		texUnits.append(diffuseUnit)

		#Normalize eye vector if necessary
		if specularUnit is not None or sphereUnit is not None or parallaxUnit is not None or envUnit is not None:
			frag = frag.replace('%normalizeEyeVec%','vec3 eVec = normalize(eyeVec);')
		else:
			frag = frag.replace('%normalizeEyeVec%','')
		
		#Generate code for light map
		if lightUnit is not None:
			frag = frag.replace('%computeLight%','vec4 lightTex = mix(vec4(1,1,1,1),'+texture(lightUnit,coordOffset=texOffset)+',lightmap_scale);')
			frag = frag.replace('%lightTex%','* lightTex')
			frag = frag.replace('%causticLight%','* lightTex.r')
			texUnits.append(lightUnit)
		else:
			frag = frag.replace('%computeLight%','')
			frag = frag.replace('%lightTex%','')
			frag = frag.replace('%causticLight%','')
		
		#Generate code for detail map
		if detailUnit is not None:
			frag = frag.replace('%detailTex%','* '+texture(detailUnit,coordOffset=texOffset)+' * 2.0')
			texUnits.append(detailUnit)
		else:
			frag = frag.replace('%detailTex%','')
		
		#Generate code for normal map
		if normalUnit is not None:
			frag = frag.replace('%computeNormal%','vec3 normal = normalize( '+texture(normalUnit,coordOffset=texOffset)+'.xyz * 2.0 - 1.0);')
			texUnits.append(normalUnit)
			normalMapUnit = normalUnit
		else:
			frag = frag.replace('%computeNormal%','vec3 normal = vec3(0,0,1);')
			normalMapUnit = diffuseUnit
		
		#Generate code for calculating eye vector for specular reflections
		if specularUnit is not None:
			frag = frag.replace('%computeSpecular%',"""float specular = 0.0;
														vec4 specularTex = """+texture(specularUnit,coordOffset=texOffset)+""";
														if(diffuse > 0.0) {
															specular = pow(max(dot(reflect(-lVec, normal), eVec), 0.0), shininess );
															alpha += specular * specularTex.r %lightAlpha%;
														}""")
			if lightUnit is not None:
				frag = frag.replace('%addSpecular%','+ (specular * specularTex * lightTex)')
				frag = frag.replace('%lightAlpha%','* lightTex.r')
			else:
				frag = frag.replace('%addSpecular%','+ (specular * specularTex)')
				frag = frag.replace('%lightAlpha%','')
			texUnits.append(specularUnit)
		else:
			frag = frag.replace('%computeSpecular%','')
			frag = frag.replace('%addSpecular%','')
			
		#Generate code for sphere map
		if sphereUnit is not None:
			code = """
			vec3 r = reflect(-eVec, normal);
			float m = 2.0 * sqrt(r.x * r.x + r.y * r.y + (r.z + 1.0) * (r.z + 1.0));
			vec4 reflectColor = """+textureWithCoord(sphereUnit,'vec2(r.x / m + 0.5,r.y / m + 0.5)')+""";
			"""
			if specularUnit is not None:
				code += 'diffuseTex = mix(diffuseTex,reflectColor,reflectColor.a * specularTex.r);\n'
				code += 'alpha += reflectColor.a * specularTex.r;\n'
			else:
				code += 'diffuseTex = mix(diffuseTex,reflectColor,reflectColor.a);\n'
				code += 'alpha += reflectColor.a;\n'
			frag = frag.replace('%computeReflection%',code)
			texUnits.append(sphereUnit)
		else:
			frag = frag.replace('%computeReflection%','')
			
		#Generate code for environment map
		if envUnit is not None:
			code = """
			{
			vec3 r = reflect(-eVec, normal);
			float m = 2.0 * sqrt(r.x * r.x + r.y * r.y + (r.z + 1.0) * (r.z + 1.0));
			vec4 envColor = """+textureWithCoord(envUnit,'vec3(r.x / m + 0.5,r.y / m + 0.5,r.z / m + 0.5)',cubeMap=True)+""";
			"""
			if specularUnit is not None:
				code += 'diffuseTex = mix(diffuseTex,envColor,envColor.a * specularTex.r);\n'
			else:
				code += 'diffuseTex = mix(diffuseTex,envColor,envColor.a);\n'
			code += '}'
			frag = frag.replace('%computeEnvmap%',code)
			texUnits.append(envUnit)
			texUnitType[envUnit] = 'samplerCube'
		else:
			frag = frag.replace('%computeEnvmap%','')

	else:
		
		#Determine how many blend units are being used
		blendUnits = [i for i in xrange(MAX_BLEND_UNITS) if units.get(DIFFUSE_MAP[i]) is not None]

		#Make sure we have at least one blend unit
		if not blendUnits:
			viz.logError('** ERROR: Material requires a diffuse map: ',material)
			return None
		
		frag = """
		varying vec3 lightVec;
		varying vec3 eyeVec;
		uniform bool refractDepth;
		uniform float ambient;
		uniform float lightmap_scale;
		uniform float fog;
		uniform float caustic;
		
		%texSamplers%
		
		void main (void)
		{	
			float shininess = 30.0;
			float lightIntensity = 1.0;
			float diffuse;
			float specular;
			float alpha;
			vec3 normal;
			vec3 lVec = normalize(lightVec);
			%normalizeEyeVec%
			vec4 finalColor = vec4(0,0,0,0);
			vec4 tempColor;
			vec4 lightTex;
			vec4 specularTex;

			%blendCode%
			
			alpha = finalColor.a;
			
			gl_FragColor = finalColor;
			
			if(caustic != 0.0) {
				gl_FragColor = gl_FragColor + (%causticTex% * diffuse * caustic * lightIntensity);
			}
			
			gl_FragColor.a = alpha;
			
			if(fog != 0.0) {
				float f = exp2(fog * gl_FogFragCoord);
				f = clamp(f, 0.0, 1.0);
				gl_FragColor = mix(gl_Fog.color, gl_FragColor, f);
				if(alpha == 0.0) {
					gl_FragColor.a = alpha;
				}
			}
			
			if(refractDepth) {
				gl_FragColor.a = gl_Color.a;
			}
		}
		"""
		
		needEyeVec = False
		
		#Add blend unit
		texUnits.append(blendUnit)
		
		#Code for doing actual blending
		blendCode = 'vec4 blendColor = '+texture(blendUnit)+';\n'
		
		#Iterate through blend units
		for i in blendUnits:
			
			#Retrieve material units from map
			diffuseUnit = units.get(DIFFUSE_MAP[i])
			normalUnit = units.get(NORMAL_MAP[i])
			lightUnit = units.get(LIGHT_MAP[i])
			specularUnit = units.get(SPECULAR_MAP[i])
			detailUnit = units.get(DETAIL_MAP[i])
			sphereUnit = units.get(SPHERE_MAP[i])

			#blendCode += 'if(blendColor['+str(i)+'] != 0.0) {\n' #Causes strange artifacts on polygon borders
			
			#Generate normal code
			if normalUnit is not None:
				texUnits.append(normalUnit)
				blendCode += 'normal = normalize( '+texture(normalUnit)+'.xyz * 2.0 - 1.0);\n'
				normalMapUnit = normalUnit
			else:
				blendCode += 'normal = vec3(0,0,1);\n'
				normalMapUnit = diffuseUnit
				
			#Generate code for calculating diffuse amount
			blendCode += 'diffuse = max( dot(lVec, normal), 0.0 );\n'
			
			#Generate diffuse code
			texUnits.append(diffuseUnit)
			blendCode += 'tempColor = '+texture(diffuseUnit)+';'
			blendCode += 'alpha = tempColor.a;'
			
			#Generate lightmap code
			if lightUnit is not None:
				texUnits.append(lightUnit)
				blendCode += 'lightTex = mix(vec4(1,1,1,1),'+texture(lightUnit)+',lightmap_scale);\n'
				blendCode += 'lightIntensity *= lightTex.r;\n'
				
			#Generate specular code
			if specularUnit is not None:
				texUnits.append(specularUnit)
				code = """
				specular = 0.0;
				specularTex = """+texture(specularUnit)+""";
				if(diffuse > 0.0) {
					specular = pow(max(dot(reflect(-lVec, normal), eVec), 0.0), shininess );
					alpha += specular * specularTex.r %lightAlpha%;
				}
				"""
				if lightUnit is not None:
					code = code.replace('%lightAlpha%','* lightTex.r')
				else:
					code = code.replace('%lightAlpha%','')
				blendCode += code
				needEyeVec = True
			
			#Generate code for sphere map
			if sphereUnit is not None:
				texUnits.append(sphereUnit)
				code = """
				vec3 r = reflect(-eVec, normal);
				float m = 2.0 * sqrt(r.x * r.x + r.y * r.y + (r.z + 1.0) * (r.z + 1.0));
				vec4 reflectColor = """+textureWithCoord(sphereUnit,'vec2(r.x / m + 0.5,r.y / m + 0.5)')+""";"""
				if specularUnit is not None:
					code += 'tempColor = mix(tempColor,reflectColor,reflectColor.a * specularTex.r);\n'
				else:
					code += 'tempColor = mix(tempColor,reflectColor,reflectColor.a);\n'
				blendCode += code
				needEyeVec = True
			
			#Add lightmap texture to diffuse
			if lightUnit is not None:
				blendCode += 'tempColor *= lightTex;\n'
			
			#Generate detailmap code
			if detailUnit is not None:
				texUnits.append(detailUnit)
				blendCode += 'tempColor *= '+texture(detailUnit)+' * 2.0;\n'

			#Calculate final color
			blendCode += 'tempColor = (diffuse * tempColor) + (ambient * tempColor);\n'
			
			#Add specular color
			if specularUnit is not None:
				if lightUnit is not None:
					blendCode += 'tempColor += specular * specularTex * lightTex;\n'
				else:
					blendCode += 'tempColor += specular * specularTex;\n'
				
			#Add to final color
			blendCode += 'tempColor.a = alpha;\n'
			blendCode += 'finalColor += tempColor * blendColor['+str(i)+'];\n'
			
			#blendCode += '}\n'
		
		#Insert blending code
		frag = frag.replace('%blendCode%',blendCode)
		
		#Normalize eye vector if necessary
		if needEyeVec:
			frag = frag.replace('%normalizeEyeVec%','vec3 eVec = normalize(eyeVec);')
		else:
			frag = frag.replace('%normalizeEyeVec%','')

	#Generate code for copying texture coordinates
	vert = vert.replace('%copyTexCoords%',''.join([texCoordCopy(u) for u in texUnits]))
	
	#Generate code for calculating caustics texture coordinates
	vert = vert.replace('%causticCoord%',texCoord(causticUnit))

	#Generate code for declaring sampler uniforms
	frag = frag.replace('%texSamplers%','\n'.join(['uniform ' + texUnitType.get(u,'sampler2D') + ' ' +_texUniform[u].getName()+';' for u in texUnits]))

	#Generate code for getting caustic texture
	frag = frag.replace('%causticTex%',texture(causticUnit));

	#Create shader
	shader = viz.addShader(vert=vert,frag=frag,flag=viz.SHADER_TANGENT)

	#Initialize flag for caustic unit
	shader.causticUnit = causticUnit

	#Initialize flag that tells whether texture coords need to be packed
	shader.packTexCoord = False
	
	#Save texture unit used to generate tangent data
	shader.normalMapUnit = normalMapUnit
	
	#Add uniforms to shader
	for u in texUnits:
		if u >= MAX_TEXCOORD_UNITS:
			shader.packTexCoord = True
		shader.attach(_texUniform[u])
	
	#Cache shader
	_shaderCache[material] = shader
	
	#Log shader
	if LOG_SHADERS:
		f = open(material+'.vert','w')
		f.write(vert)
		f.close()
		f = open(material+'.frag','w')
		f.write(frag)
		f.close()
	
	return shader

def _processAvatar(model):
	
	#Set of mesh names with specular maps
	specMesh = set()
	
	#List of mesh names on the avatar
	meshList = model.getMeshList()

	#Add avatar cfg directory to path list
	dir = os.path.dirname(viz.res.getFullPath(model.getFilename())) + '\\'
	pathList = viz.res.getPathList()
	pathList.append(dir)
	viz.res.setPathList(pathList)

	#Process specular map config variable
	spec = model.getConfigValue('specular_map')
	for s in spec.split('|'):
		val = s.split(':')
		if len(val) == 2:
			tex = viz.addTexture(val[1],useCache=True)
			if tex.valid():
				if val[0] == 'all':
					model.texture(tex,unit=1)
					specMesh.update(meshList)
				else:
					model.texture(tex,val[0],unit=1)
					specMesh.add(val[0])
					
	#Restore original path list
	pathList.pop()
	viz.res.setPathList(pathList)

	for mesh in meshList:

		#Check if mesh has specular map
		if mesh in specMesh:
			name = 'AvatarShaderSpecularDiffuse'
			specular = True
		else:
			name = 'AvatarShaderDiffuse'
			specular = False

		#See if shader is already cached
		if name in _shaderCache:
			shader = _shaderCache[name]
		else:
		
			vert = """
			varying vec3 lightVec;
			varying vec3 eyeVec;
			varying vec3 normal;
			uniform bool refractDepth;
			uniform int light;
			uniform float caustic;
			uniform float causticScale;
			uniform mat4 osg_ViewMatrixInverse;
		
			#define WATER_HEIGHT	0.5
		
			void main(void)
			{
				gl_Position = ftransform();
				gl_ClipVertex = gl_ModelViewMatrix * gl_Vertex;
				gl_FogFragCoord = abs(gl_ClipVertex.z);
				
				gl_TexCoord[0].xy = gl_MultiTexCoord0.xy;
				
				if(caustic != 0.0) {
					//Caustic texcoord derived from world xz vertex coordinate
					vec4 worldVertex = osg_ViewMatrixInverse * gl_ClipVertex;
					gl_TexCoord[0].zw = causticScale * worldVertex.xz;
				}
				
				if(refractDepth) {
					vec4 worldVertex = osg_ViewMatrixInverse * gl_ClipVertex;
					gl_FrontColor.a = clamp((WATER_HEIGHT - worldVertex.y) / 2.0,0.0,1.0);
				}
				
				//Save light vector in eye space
				if(gl_LightSource[light].position.w == 0.0) {
					lightVec = gl_LightSource[light].position.xyz;
				} else {
					lightVec = vec3(gl_LightSource[light].position-gl_ClipVertex);
				}
				
				//Save eye vector in eye space
				eyeVec = -vec3(gl_ClipVertex);
				
				//Save normal in eye space
				normal = gl_NormalMatrix * gl_Normal;
			}
			"""
				
			frag = """
			varying vec3 lightVec;
			varying vec3 eyeVec;
			varying vec3 normal;
			uniform bool refractDepth;
			uniform float ambient;
			uniform float fog;
			uniform float caustic;
			
			%texSamplers%
			
			void main (void)
			{	
				float shininess = 30.0;
				vec3 nVec = normalize(normal);
				vec3 lVec = normalize(lightVec);

				float diffuse = max( dot(lVec, nVec), 0.0 );
				
				vec4 color = %diffuseTex%;
				float alpha = color.a * gl_FrontMaterial.diffuse.a;
				
				vec4 finalColor = (diffuse * color) + (ambient * color);
				
				%specular%
				
				gl_FragColor = finalColor;
				
				if(caustic != 0.0) {
					gl_FragColor = gl_FragColor + (%causticTex% * diffuse * caustic);
				}
				
				gl_FragColor.a = alpha;
				
				if(fog != 0.0) {
					float f = exp2(fog * gl_FogFragCoord);
					f = clamp(f, 0.0, 1.0);
					gl_FragColor = mix(gl_Fog.color, gl_FragColor, f);
					if(alpha == 0.0) {
						gl_FragColor.a = alpha;
					}
				}
				
				if(refractDepth) {
					gl_FragColor.a = gl_Color.a;
				}
			}
			"""
			
			#List of texture units used
			texUnits = [0]
			
			#Calculate code for computing specular color
			specularCode = ''
			if specular:
				specularCode = """
				if(diffuse > 0.0) {
					finalColor += """+texture(1,0)+""" * pow(max(dot(reflect(-lVec, nVec), normalize(eyeVec)), 0.0), shininess );
				}"""
				texUnits.append(1)
			
			#Add caustic texture unit
			causticUnit = len(texUnits)
			texUnits.append(causticUnit)
			frag = frag.replace('%causticTex%',texture(causticUnit,1))
			
			#Generate code for declaring sampler uniforms
			frag = frag.replace('%texSamplers%','\n'.join(['uniform sampler2D '+_texUniform[u].getName()+';' for u in texUnits]))
			
			#Generate code for getting diffuse texture
			frag = frag.replace('%diffuseTex%',texture(0))
			
			#Generate code for specular
			frag = frag.replace('%specular%',specularCode)
			
			#Create shader
			shader = viz.addShader(vert=vert,frag=frag)
			
			#Save caustic unit in shader
			shader.causticUnit = causticUnit
			
			#Add uniforms to shader
			for u in texUnits:
				shader.attach(_texUniform[u])

			#Cache shader
			_shaderCache[name] = shader
			
			#Log shader
			if LOG_SHADERS:
				f = open(name+'.vert','w')
				f.write(vert)
				f.close()
				f = open(name+'.frag','w')
				f.write(frag)
				f.close()
			
		#Apply shader to mesh
		model.apply(shader,mesh)
		if _causticTexture is not None:
			model.texture(_causticTexture,mesh,shader.causticUnit)

###############################################
############## Public Interface ###############
###############################################

def process(model):
	"""Scan material name of model for shader definitions and apply them"""
	
	#Apply global uniforms to model
	for u in _globalUniforms:
		model.apply(u)
	
	#Special case for avatars
	if isinstance(model,viz.VizAvatar):
		_processAvatar(model)
		model.hint(viz.COMPRESS_TEXTURE_HINT | viz.FREE_TEXTURE_MEMORY_HINT | viz.PRELOAD_HINT | viz.ALLOW_NPOT_TEXTURE_HINT)
		return
	
	for name in model.getNodeNames():
		s = name.split('_')
		if len(s) > 1:
			format = s[-1]
			if len(format) > 0 and format[0] == '[' and format[-1] == ']':
				mat = format[1:-1]
				shader = _getShader(mat,name)
				if shader is not None:
					viz.setOption('viz.shader.normal_map_unit',shader.normalMapUnit)
					model.apply(shader,name)
					if _causticTexture is not None:
						model.texture(_causticTexture,name,shader.causticUnit)
					if shader.packTexCoord:
						model.hint(viz.PACK_TEXCOORD_HINT,name)

		#Check if node has animation enabled
		if ANIMATE_FLAG in name:
			model.apply(_animationOnUniform,name)
	
	model.hint(viz.FREE_TEXTURE_MEMORY_HINT | viz.PRELOAD_HINT | viz.ALLOW_NPOT_TEXTURE_HINT)
	
def setLightNumber(num):
	"""Set the light number to use for all lighting calculation"""
	_lightUniform.set(num)

def setAmbientIntensity(val):
	"""Set the global ambient intensity"""
	_ambientUniform.set(val)

def setLightmapScale(val):
	"""Set scale factor for lightmaps"""
	_lightMapUniform.set(val)

def setFog(val):
	"""Set the global fog density value. Use 0 to disable fog"""
	#pre multiply with LOG2E for performance boost
	_fogUniform.set(-val*1.442695)

def setCaustic(texture,intensity=CAUSTIC_INTENSITY,scale=CAUSTIC_SCALE):
	"""Set the caustics texture"""
	global _causticTexture
	_causticTexture = texture
	if _causticTexture is None:
		_causticUniform.set(0)
	else:
		_causticUniform.set(intensity)
		_causticScaleUniform.set(scale)

class WaterEffect(object):
	
	def __init__(self,plane,height=0,size=[512,512]):
	
		SIZE = [512,512]
		
		REFLECT_MASK = viz.LAST_MASK << 1

		#Use same septh texture for both render nodes
		depthTex = viz.addRenderTexture(format=viz.TEX_DEPTH)
		
		#Setup reflection texture
		reflectTex = viz.addRenderTexture()
		reflect = viz.addRenderNode(size=SIZE)
		reflect.attachTexture(reflectTex)
		reflect.attachTexture(depthTex,viz.RENDER_DEPTH)
		reflect.setMatrix(viz.Matrix.translate(0,-height,0)*viz.Matrix.scale(1,-1,1)*viz.Matrix.translate(0,height,0))
		reflect.setInheritView(True,viz.POST_MULT)
		reflect.disable(viz.CULL_FACE,op=viz.OP_SET_OVERRIDE)
		reflect.clipPlane([0,-1,0,-height]) #SET_OVERRIDE
		reflect.setCullMask(REFLECT_MASK)
		
		#Setup refraction texture
		refractTex = viz.addRenderTexture()
		refract = viz.addRenderNode(size=SIZE)
		refract.attachTexture(refractTex)
		refract.attachTexture(depthTex,viz.RENDER_DEPTH)
		refract.clipPlane([0,-1,0,-height-0.05]) #SET_OVERRIDE
		refract.setCullMask(REFLECT_MASK)
		refract.apply(_refractDepthOnUniform,op=viz.OP_SET_OVERRIDE)
		
		vert = """
		attribute vec3 Tangent;
		uniform float osg_FrameTime;
		uniform int light;
		
		#define WAVE_SCALE 0.01
		#define WAVE_SPEED 0.01
		
		void main(void)
		{
			gl_Position = ftransform();

			vec2 fTranslation= vec2(mod(osg_FrameTime, 100.0)*WAVE_SPEED, 0.0);
			vec2 vTexCoords = gl_Vertex.xz*WAVE_SCALE;

			// Scale texture coordinates to get mix of low/high frequency details
			gl_TexCoord[1].xy = vTexCoords.xy+fTranslation*2.0;
			gl_TexCoord[2].xy = vTexCoords.xy*2.0+fTranslation*4.0;
			gl_TexCoord[3].xy = vTexCoords.xy*4.0+fTranslation*2.0;
			gl_TexCoord[4].xy = vTexCoords.xy*8.0+fTranslation;  
		
			// perspective corrected projection
			gl_TexCoord[1].zw = gl_Position.ww;
			gl_TexCoord[5].xy = (gl_Position.xy + gl_Position.w)*0.5;
			gl_TexCoord[5].zw =  vec2(1, gl_Position.w);
		
			// get tangent space basis    
			vec3 n = normalize(gl_NormalMatrix * gl_Normal);
			vec3 t = normalize(gl_NormalMatrix * Tangent);
			vec3 b = cross(n, t);

			// compute tangent space light vector
			vec3 tmpVec = -gl_LightSource[light].position.xyz;
			gl_TexCoord[6].x = dot(tmpVec, t);
			gl_TexCoord[6].y = dot(tmpVec, b);
			gl_TexCoord[6].z = dot(tmpVec, n);

			// compute tangent space eye vector
			tmpVec = -vec3(gl_ModelViewMatrix * gl_Vertex);
			gl_TexCoord[0].x = dot(tmpVec, t);
			gl_TexCoord[0].y = dot(tmpVec, b);
			gl_TexCoord[0].z = dot(tmpVec, n);
		}
		"""
		
		frag = """
		uniform sampler2D water_normal;
		uniform sampler2D water_reflection;
		uniform sampler2D water_refraction;
		uniform float refract;
		
		#define FADE_DIST 10.0
		#define REFRACT_SCALE	vec3(0.02, 0.02, 1.0)
		#define REFLECT_SCALE	vec3(0.1, 0.1, 1.0)
		
		void main(void)
		{
			vec3 vEye = normalize(gl_TexCoord[0].xyz);

			// Get bump layers
			vec3 vBumpTexA = texture2D(water_normal, gl_TexCoord[1].xy).xyz;
			vec3 vBumpTexB = texture2D(water_normal, gl_TexCoord[2].xy).xyz;
			vec3 vBumpTexC = texture2D(water_normal, gl_TexCoord[3].xy).xyz;
			vec3 vBumpTexD = texture2D(water_normal, gl_TexCoord[4].xy).xyz;

			// Average bump layers
			vec3 vBumpTex = normalize(2.0 * (vBumpTexA + vBumpTexB + vBumpTexC + vBumpTexD)-4.0);

			// Apply individual bump scale for refraction and reflection
			vec3 vRefrBump = vBumpTex * REFRACT_SCALE;
			vec3 vReflBump = vBumpTex * REFLECT_SCALE;

			// Compute projected coordinates
			vec2 vProj = (gl_TexCoord[5].xy/gl_TexCoord[5].w);
			vec4 vReflection = texture2D(water_reflection, vProj.xy + vReflBump.xy);
			vec4 vRefraction = texture2D(water_refraction, vProj.xy + vRefrBump.xy);

			// Compute Fresnel term
			float NdotL = max(dot(vEye, vReflBump), 0.0);
			float facing = (1.0 - NdotL);
			float fresnelBias = 0.2;
			float fresnelPow = 5.0;
			float fresnel = max(fresnelBias + (1.0-fresnelBias)*pow(facing, fresnelPow), 0.0);

			// Compute specular color
			vec3 specular = vec3(0,0,0);
			if(NdotL > 0.0) {
				specular = vec3(1,1,1) * pow(max(dot(reflect(normalize(gl_TexCoord[6].xyz), vReflBump), vEye), 0.0), 30.0 );
			}

			// Use distance to lerp between refraction and deep water color
			//float fDistScale = clamp(FADE_DIST/gl_TexCoord[1].w,0.0,1.0)*refract;
			float fDistScale = (1.0-vRefraction.a)*refract;
			vec3 WaterDeepColor = mix(vec3(0.0, 0.1, 0.125),vRefraction.xyz,fDistScale);

			// Lerp between water color and deep water color
			vec3 waterColor = mix(WaterDeepColor,vec3(0, 0.1, 0.15),facing*vRefraction.a);
			vec3 cReflect = (vRefraction.a * fresnel * vReflection).xyz;

			// final water = reflection_color * fresnel + water_color
			gl_FragColor = vec4(cReflect + waterColor + specular, 1);  
		}
		"""
		shader = viz.addShader(vert=vert,frag=frag,flag=viz.SHADER_TANGENT)
		uniformList = [ viz.addUniformInt('water_normal',0)
						, viz.addUniformInt('water_reflection',1)
						, viz.addUniformInt('water_refraction',2) ]
		refractUniform = viz.addUniformFloat('refract',1.0)
		shader.attach( *uniformList )
		shader.attach(refractUniform)
		shader.attach(_lightUniform)
		plane.apply(shader)
		
		#Apply reflection/refraction/normal texture to plane
		waves = viz.add('waves.dds',wrap=viz.REPEAT)
		plane.texture(waves,unit=0)
		plane.texture(reflectTex,unit=1)
		plane.texture(refractTex,unit=2)
		
		#Remove reflect mask from plane so it isn't drawn during reflect/refract stage
		plane.setMask(REFLECT_MASK,mode=viz.MASK_REMOVE)
		
		#Populate remove list
		removeList = []
		removeList.append(waves)
		removeList.append(depthTex)
		removeList.append(reflectTex)
		removeList.append(refractTex)
		removeList.append(reflect)
		removeList.append(refract)
		removeList.append(shader)
		removeList.append(refractUniform)
		removeList.extend(uniformList)
		
		#Save attributes
		self.removeList = removeList
		self.reflectNode = reflect
		self.refractNode = refract
		self.refractUniform = refractUniform
		
		#viz.addTexQuad(viz.SCREEN,size=200,texture=reflectTex,align=viz.TEXT_LEFT_BOTTOM)
		#viz.addTexQuad(viz.SCREEN,size=200,texture=refractTex,align=viz.TEXT_LEFT_BOTTOM,pos=(0.3,0,0))
	
		self.REFLECT_MASK = REFLECT_MASK

	def setLowPolyModel(self,high,low):
		high.setMask(self.REFLECT_MASK,mode=viz.MASK_REMOVE)
		low.setMask(self.REFLECT_MASK)
	
	def setRefraction(self,intensity):
		self.refractUniform.set(intensity)
		self.refractNode.visible(intensity>0)
	
	def setEnabled(self,val):
		if val:
			self.enable()
		else:
			self.disable()
		
	def enable(self):
		self.reflectNode.visible(viz.ON)
		self.refractNode.visible(viz.ON)
	
	def disable(self):
		self.reflectNode.visible(viz.OFF)
		self.refractNode.visible(viz.OFF)
		
	def remove(self):
		for x in self.removeList:
			x.remove()
		del self.removeList[:]

class WaterRefraction(object):
	
	def __init__(self,node,size=[256,256]):

		REFRACT_MASK = viz.LAST_MASK << 1
		
		#Get height of water plane
		height = node.getBoundingBox(viz.ABS_GLOBAL,node=REFRACT_NODE).center[1]
		
		#Remove refraction mask from water plane
		node.setMask(REFRACT_MASK,node=REFRACT_NODE,mode=viz.MASK_REMOVE)
		
		#Setup refraction texture
		refractTex = viz.addRenderTexture()
		refract = viz.addRenderNode(size=size)
		refract.attachTexture(refractTex)
		refract.clipPlane([0,-1,0,-height-0.3]) #SET_OVERRIDE
		refract.setScene(None)
		refract.setCullMask(REFRACT_MASK)
		
		#Have render node only render node
		node.duplicate(scene=viz.MainScene,parent=refract)
		
		vert = """
		attribute vec3 Tangent;
		uniform float osg_FrameTime;
		uniform int light;
		
		#define WAVE_SCALE 0.001
		#define WAVE_SPEED 0.005
		
		void main(void)
		{
			gl_Position = ftransform();

			vec2 fTranslation= vec2(mod(osg_FrameTime, 100.0)*WAVE_SPEED, 0.0);
			vec2 vTexCoords = gl_Vertex.xz*WAVE_SCALE;

			// Scale texture coordinates to get mix of low/high frequency details
			gl_TexCoord[1].xy = vTexCoords.xy+fTranslation*2.0;
			gl_TexCoord[2].xy = -vTexCoords.xy*2.0+fTranslation*4.0;
			gl_TexCoord[3].xy = -vTexCoords.xy*4.0+fTranslation*2.0;
			gl_TexCoord[4].xy = vTexCoords.xy*8.0+fTranslation;  
		
			// perspective corrected projection
			gl_TexCoord[1].zw = gl_Position.ww;
			gl_TexCoord[5].xy = (gl_Position.xy + gl_Position.w)*0.5;
			gl_TexCoord[5].zw =  vec2(1, gl_Position.w);
		
			// get tangent space basis    
			vec3 n = normalize(gl_NormalMatrix * gl_Normal);
			vec3 t = normalize(gl_NormalMatrix * Tangent);
			vec3 b = cross(n, t);

			// compute tangent space light vector
			vec3 tmpVec = -gl_LightSource[light].position.xyz;
			gl_TexCoord[6].x = dot(tmpVec, t);
			gl_TexCoord[6].y = dot(tmpVec, b);
			gl_TexCoord[6].z = dot(tmpVec, n);

			// compute tangent space eye vector
			tmpVec = -vec3(gl_ModelViewMatrix * gl_Vertex);
			gl_TexCoord[0].x = dot(tmpVec, t);
			gl_TexCoord[0].y = dot(tmpVec, b);
			gl_TexCoord[0].z = dot(tmpVec, n);
		}
		"""
		
		frag = """
		uniform sampler2D water_normal;
		uniform sampler2D water_refraction;
		
		#define FADE_DIST 10.0
		#define REFRACT_SCALE	vec3(0.02, 0.02, 1.0)
		
		void main(void)
		{
			vec3 vEye = normalize(gl_TexCoord[0].xyz);

			// Get bump layers
			vec3 vBumpTexA = texture2D(water_normal, gl_TexCoord[1].xy).xyz;
			vec3 vBumpTexB = texture2D(water_normal, gl_TexCoord[2].xy).xyz;
			vec3 vBumpTexC = texture2D(water_normal, gl_TexCoord[3].xy).xyz;
			vec3 vBumpTexD = texture2D(water_normal, gl_TexCoord[4].xy).xyz;

			// Average bump layers
			vec3 vBumpTex = normalize(2.0 * (vBumpTexA + vBumpTexB + vBumpTexC + vBumpTexD)-4.0);

			// Apply individual bump scale for refraction and reflection
			vec3 vRefrBump = vBumpTex * REFRACT_SCALE;

			// Compute projected coordinates
			vec2 vProj = (gl_TexCoord[5].xy/gl_TexCoord[5].w);
			vec4 vRefraction = texture2D(water_refraction, vProj.xy + vRefrBump.xy);

			// Compute Fresnel term
			float NdotL = max(dot(vEye, vBumpTex), 0.0);
			float facing = (1.0 - NdotL);
			float fresnelBias = 0.2;
			float fresnelPow = 5.0;
			float fresnel = max(fresnelBias + (1.0-fresnelBias)*pow(facing, fresnelPow), 0.0);

			// Compute specular color
			vec3 specular = vec3(0,0,0);
			if(NdotL > 0.0) {
				specular = vec3(1,1,1) * pow(max(dot(reflect(normalize(gl_TexCoord[6].xyz), vBumpTex), vEye), 0.0), 80.0 );
			}
			
			// Lerp between water color and deep water color
			vec3 WaterColor = vec3(0, 0.1, 0.15);
			vec3 waterColor = vRefraction.xyz;//(WaterColor * facing + WaterDeepColor * (1.0 - facing));

			// final water = reflection_color * fresnel + water_color
			gl_FragColor = vec4(waterColor + specular, 1);  
		}
		"""
		shader = viz.addShader(vert=vert,frag=frag)
		uniformList = [ viz.addUniformInt('water_normal',0)
						, viz.addUniformInt('water_refraction',1) ]
		shader.attach( *uniformList )
		shader.attach(_lightUniform)
		node.apply(shader,node=REFRACT_NODE)
		
		#Apply reflection/refraction/normal texture to plane
		waves = viz.add('waves.dds',wrap=viz.REPEAT)
		node.texture(waves,node=REFRACT_NODE,unit=0)
		node.texture(refractTex,node=REFRACT_NODE,unit=1)
		
		#Populate remove list
		removeList = []
		removeList.append(waves)
		removeList.append(refractTex)
		removeList.append(refract)
		removeList.append(shader)
		removeList.extend(uniformList)
		
		#Save attributes
		self.removeList = removeList
		
	def remove(self):
		for x in self.removeList:
			x.remove()
		del self.removeList[:]
		
class WaterBeams(object):
	
	def __init__(self,**kw):
		viz.startlayer(viz.QUADS)
		self.node = viz.endlayer(**kw)
		
		vert = """
		uniform int light;
		uniform float osg_FrameTime;
		uniform mat4 osg_ViewMatrixInverse;
		varying float alpha;
		void main(void)
		{
			/* Parameters are encoded in vertex color
			   r - Animation time offset
			   g - Animation speed
			   b - Beam length
			   a - Beam width
			*/
			
			//Get light vector in world coordinates
			vec4 lightVec = osg_ViewMatrixInverse * gl_LightSource[light].position.xyzw;
			
			//Compute alpha based on time
			alpha = sin((osg_FrameTime+gl_Color.r)*gl_Color.g);
			
			//Extrude beam along light vector. Animate length based on alpha.
			vec4 glVertex = gl_Vertex;
			glVertex += -normalize(lightVec)*gl_MultiTexCoord0.y*(gl_Color.b+gl_Color.b*0.1*alpha);
			
			//Extrude beam along billboard vector. Animate width based on alpha
			vec3 tmpVec = cross(osg_ViewMatrixInverse[3].xyz - glVertex.xyz,lightVec.xyz);
			tmpVec = normalize(tmpVec);
			glVertex.xyz += tmpVec*(gl_MultiTexCoord0.x*2.0-1.0)*alpha*gl_Color.a;
			
			gl_Position = ftransform();
			gl_ClipVertex = gl_ModelViewMatrix * glVertex;
			gl_FogFragCoord = abs(gl_ClipVertex.z);
			gl_TexCoord[0].xy = gl_MultiTexCoord0.xy;
		}
		"""

		frag = """
		varying float alpha;
		uniform float fog;
		void main(void)
		{
			float xoffset = 0.5 - abs(gl_TexCoord[0].x - 0.5);
			float yoffset = abs(gl_TexCoord[0].y - 0.5);
			if(yoffset < 0.4) {
				yoffset = 1.0;
			} else {
				yoffset = (0.5-yoffset)/0.1;
			}
			float a = alpha*0.1*xoffset*yoffset;
			gl_FragColor = vec4(1,1,1,a);
			
			if(fog != 0.0) {
				float f = exp2(fog * gl_FogFragCoord * 0.4);
				f = clamp(f, 0.0, 1.0);
				gl_FragColor = mix(gl_Fog.color, gl_FragColor, f);
			}

			gl_FragColor.a = a;
		}
		"""
		
		shader = viz.addShader(vert=vert,frag=frag)
		self.node.apply(shader)
		self.node.apply(_lightUniform)
		self.node.apply(_fogUniform)
		self.node.disable(viz.CULLING)
		self.node.enable(viz.BLEND)
		self.node.draworder(20) #Draw after other models
		self.node.blendFunc(viz.GL_SRC_ALPHA,viz.GL_ONE)
		
		#Initialize remove list
		self.removeList = []
		self.removeList.append(shader)
		self.removeList.append(self.node)
		
	def addBeam(self,pos,length,width):
		normal = viz.Vector(vizmat.GetRandom(-1,1),0,vizmat.GetRandom(-1,1),normalize=True)
		color = [vizmat.GetRandom(0,10),vizmat.GetRandom(2,3),length,width]
		self.node.addVertex(pos,color=color,normal=normal,texCoord=[0,0])
		self.node.addVertex(pos,color=color,normal=normal,texCoord=[0,1])
		self.node.addVertex(pos,color=color,normal=normal,texCoord=[1,1])
		self.node.addVertex(pos,color=color,normal=normal,texCoord=[1,0])
		
	def remove(self):
		for x in self.removeList:
			x.remove()
		del self.removeList[:]
		
class WaterSurface(object):
	
	def __init__(self,height=0,**kw):
		self.node = viz.addTexQuad(**kw)
		self.node.translate(0,height,0)
		self.node.setEuler(0,90,0)
		self.node.setScale(50,50,1)
		
		vert = """
		varying vec3 lightVec;
		varying vec3 eyeVec;
		varying vec3 normal;
		uniform int light;
		uniform float caustic;
		uniform float causticScale;
		uniform mat4 osg_ViewMatrixInverse;

		void main(void)
		{
			gl_Position = ftransform();
			gl_ClipVertex = gl_ModelViewMatrix * gl_Vertex;
			gl_FogFragCoord = abs(gl_ClipVertex.z);
			gl_TexCoord[0].xy = gl_MultiTexCoord0.xy;
		}
		"""
		
		frag = """
		uniform sampler2D permTexture;
		uniform sampler1D simplexTexture;
		uniform float osg_FrameTime;
		uniform float fog;
		/*
		 * To create offsets of one texel and one half texel in the
		 * texture lookup, we need to know the texture image size.
		 */
		#define ONE 0.00390625
		#define ONEHALF 0.001953125
		// The numbers above are 1/256 and 0.5/256, change accordingly
		// if you change the code to use another texture size.

		/*
		 * 3D simplex noise. Comparable in speed to classic noise, better looking.
		 */
		float snoise(vec3 P) {

			// The skewing and unskewing factors are much simpler for the 3D case
			#define F3 0.333333333333
			#define G3 0.166666666667

			// Skew the (x,y,z) space to determine which cell of 6 simplices we're in
			float s = (P.x + P.y + P.z) * F3; // Factor for 3D skewing
			vec3 Pi = floor(P + s);
			float t = (Pi.x + Pi.y + Pi.z) * G3;
			vec3 P0 = Pi - t; // Unskew the cell origin back to (x,y,z) space
			Pi = Pi * ONE + ONEHALF; // Integer part, scaled and offset for texture lookup

			vec3 Pf0 = P - P0;  // The x,y distances from the cell origin

			// For the 3D case, the simplex shape is a slightly irregular tetrahedron.
			// To find out which of the six possible tetrahedra we're in, we need to
			// determine the magnitude ordering of x, y and z components of Pf0.
			// The method below is explained briefly in the C code. It uses a small
			// 1D texture as a lookup table. The table is designed to work for both
			// 3D and 4D noise, so only 8 (only 6, actually) of the 64 indices are
			// used here.
			float c1 = (Pf0.x > Pf0.y) ? 0.5078125 : 0.0078125; // 1/2 + 1/128
			float c2 = (Pf0.x > Pf0.z) ? 0.25 : 0.0;
			float c3 = (Pf0.y > Pf0.z) ? 0.125 : 0.0;
			float sindex = c1 + c2 + c3;
			vec3 offsets = texture1D(simplexTexture, sindex).rgb;
			vec3 o1 = step(0.375, offsets);
			vec3 o2 = step(0.125, offsets);

			// Noise contribution from simplex origin
			float perm0 = texture2D(permTexture, Pi.xy).a;
			vec3  grad0 = texture2D(permTexture, vec2(perm0, Pi.z)).rgb * 4.0 - 1.0;
			float t0 = 0.6 - dot(Pf0, Pf0);
			float n0;
			if (t0 < 0.0) n0 = 0.0;
			else {
				t0 *= t0;
				n0 = t0 * t0 * dot(grad0, Pf0);
			}

			// Noise contribution from second corner
			vec3 Pf1 = Pf0 - o1 + G3;
			float perm1 = texture2D(permTexture, Pi.xy + o1.xy*ONE).a;
			vec3  grad1 = texture2D(permTexture, vec2(perm1, Pi.z + o1.z*ONE)).rgb * 4.0 - 1.0;
			float t1 = 0.6 - dot(Pf1, Pf1);
			float n1;
			if (t1 < 0.0) n1 = 0.0;
			else {
				t1 *= t1;
				n1 = t1 * t1 * dot(grad1, Pf1);
			}

			// Noise contribution from third corner
			vec3 Pf2 = Pf0 - o2 + 2.0 * G3;
			float perm2 = texture2D(permTexture, Pi.xy + o2.xy*ONE).a;
			vec3  grad2 = texture2D(permTexture, vec2(perm2, Pi.z + o2.z*ONE)).rgb * 4.0 - 1.0;
			float t2 = 0.6 - dot(Pf2, Pf2);
			float n2;
			if (t2 < 0.0) n2 = 0.0;
			else {
				t2 *= t2;
				n2 = t2 * t2 * dot(grad2, Pf2);
			}

			// Noise contribution from last corner
			vec3 Pf3 = Pf0 - vec3(1.0-3.0*G3);
			float perm3 = texture2D(permTexture, Pi.xy + vec2(ONE, ONE)).a;
			vec3  grad3 = texture2D(permTexture, vec2(perm3, Pi.z + ONE)).rgb * 4.0 - 1.0;
			float t3 = 0.6 - dot(Pf3, Pf3);
			float n3;
			if(t3 < 0.0) n3 = 0.0;
			else {
				t3 *= t3;
				n3 = t3 * t3 * dot(grad3, Pf3);
			}

			// Sum up and scale the result to cover the range [-1,1]
			return 32.0 * (n0 + n1 + n2 + n3);
		}

		void main (void)
		{
			//Compute two noise values
			float n1 = snoise(vec3(80.0 * gl_TexCoord[0].xy, 0.3 * osg_FrameTime))*0.5 + 0.5;
			float n2 = snoise(vec3(40.0 * gl_TexCoord[0].xy, 0.2 * osg_FrameTime+20.0))*0.5 + 0.5;
			
			//Get distance from center
			float d = 1.0 - min(distance(vec2(0.5,0.5),gl_TexCoord[0].xy),1.0);
			
			//Mix outer/inner color based on pixel distance from center
			float p1 = 1.0 - pow(d*1.3,10.0);
			float p2 = pow(d*1.1,10.0);
			vec4 col = mix(vec4(0,0.2,0.6,1.0),vec4(0,0,0.5,1.0),p1*n1*n2);
			gl_FragColor = col + vec4(1.0,1.0,1.0,1.0)*p2*max(n1*n2,0.2);
			
			float alpha = 1.0;
			gl_FragColor.a = alpha;
			
			if(fog != 0.0) {
				float f = exp2(fog * gl_FogFragCoord * 0.4);
				f = clamp(f, 0.0, 1.0);
				gl_FragColor = mix(gl_Fog.color, gl_FragColor, f);
				if(alpha == 0.0) {
					gl_FragColor.a = alpha;
				}
			}
		}
		"""

		#Apply noise textures
		simplex = viz.addTexture('simplex.dds',type=viz.TEX_1D,filter=viz.NEAREST)
		perm = viz.addTexture('perm.dds',filter=viz.NEAREST)
		self.node.texture(simplex)
		self.node.texture(perm,unit=1)

		#Create shader/uniforms
		shader = viz.addShader(frag=frag,vert=vert)
		tex1 = viz.addUniformInt('simplexTexture',0)
		tex2 = viz.addUniformInt('permTexture',1)
		
		#Apply shaders/uniforms
		self.node.apply(shader)
		self.node.apply(tex1)
		self.node.apply(tex2)
		self.node.apply( _fogUniform )
		
		#Initialize remove list
		self.removeList = []
		self.removeList.append(self.node)
		self.removeList.append(simplex)
		self.removeList.append(perm)
		self.removeList.append(shader)
		self.removeList.append(tex1)
		self.removeList.append(tex2)

	def remove(self):
		for x in self.removeList:
			x.remove()
		del self.removeList[:]

class WaterParticles(object):
	
	def __init__(self,**kw):
		
		viz.startlayer(viz.QUADS)
		self.node = viz.endlayer(**kw)
		
		vert = """
		uniform int light;
		uniform float osg_FrameTime;
		uniform mat4 osg_ViewMatrixInverse;
		void main(void)
		{
			/* Parameters are encoded in vertex color
			   r - Animation time offset
			   g - Animation speed
			   b - Particle Size
			*/
			
			//Compute alpha based on time
			float time = (osg_FrameTime+gl_Color.r)*gl_Color.g;
			
			//Animate vertex
			vec4 glVertex = gl_Vertex;
			glVertex.xyz += gl_Normal*sin(time)*0.2;
			
			//Convert to eye space
			glVertex = gl_ModelViewMatrix * glVertex;
			
			//Extrude point
			glVertex.x += (gl_MultiTexCoord0.x*2.0-1.0)*gl_Color.b;
			glVertex.y += (gl_MultiTexCoord0.y*2.0-1.0)*gl_Color.b;
			
			//Save clip vertex in eye space
			gl_ClipVertex = glVertex;
			
			//Convert to screen coordinates
			gl_Position = gl_ProjectionMatrix * glVertex;
			gl_FogFragCoord = abs(gl_ClipVertex.z);
			gl_TexCoord[0].xy = gl_MultiTexCoord0.xy;
		}
		"""

		frag = """
		uniform float fog;
		uniform sampler2D tex;
		void main(void)
		{
			gl_FragColor = texture2D(tex,gl_TexCoord[0].xy);
			float alpha = gl_FragColor.a;
			
			if(fog != 0.0) {
				float f = exp2(fog * gl_FogFragCoord);
				f = clamp(f, 0.0, 1.0);
				gl_FragColor = mix(gl_Fog.color, gl_FragColor, f);
			}

			gl_FragColor.a = alpha;
		}
		"""
		
		tex = viz.add('floater.tga')
		texUniform = viz.addUniformInt('tex',0)
		shader = viz.addShader(vert=vert,frag=frag)
		self.node.apply(shader)
		self.node.apply(texUniform)
		self.node.apply(_fogUniform)
		self.node.disable(viz.CULLING)
		self.node.texture(tex)
		
		#Initialize remove list
		self.removeList = []
		self.removeList.append(shader)
		self.removeList.append(self.node)
		self.removeList.append(tex)
		self.removeList.append(texUniform)
		
	def addParticle(self,pos,size):
		normal = viz.Vector(vizmat.GetRandom(-1,1),vizmat.GetRandom(-1,1),vizmat.GetRandom(-1,1),normalize=True)
		color = [vizmat.GetRandom(0,10),vizmat.GetRandom(0.05,0.2),size,1]
		self.node.addVertex(pos,color=color,normal=normal,texCoord=[0,0])
		self.node.addVertex(pos,color=color,normal=normal,texCoord=[0,1])
		self.node.addVertex(pos,color=color,normal=normal,texCoord=[1,1])
		self.node.addVertex(pos,color=color,normal=normal,texCoord=[1,0])
		
	def remove(self):
		for x in self.removeList:
			x.remove()
		del self.removeList[:]

class WaterShore(object):
	
	def __init__(self):

		frag = """
		uniform sampler2D tex;
		uniform float osg_FrameTime;
		void main(void)
		{
			float baseAlpha = gl_TexCoord[0].t;
			
			float time = sin(osg_FrameTime*0.6);
			vec2 coord = gl_TexCoord[0].st;
			coord.t += (sin(coord.s)+1.0)*0.2;
			coord.t -= time * 0.4;
			vec4 s1 = texture2D(tex,coord);
			s1.a *= baseAlpha;
			
			time = sin(osg_FrameTime*0.5+3.0);
			coord = gl_TexCoord[0].st;
			coord.t += (sin(coord.s*3.0)+sin(coord.s*0.7)+sin(coord.s*0.3)+3.0)*0.1;
			coord.t -= time * 0.4;
			coord.s += 0.5;
			vec4 s2 = texture2D(tex,coord);
			s2.a *= baseAlpha;
			
			time = sin(osg_FrameTime*1.5)*0.1+0.3;
			coord = gl_TexCoord[0].st;
			coord.t -= time * 0.4;
			vec4 s3 = texture2D(tex,coord);
			s3.a *= baseAlpha;
			
			gl_FragColor = (s1 + s2 + s3);
			gl_FragColor.a *= 2.0;
		}
		"""
		
		tex = viz.addTexture('wave_wash.tga')
		tex.wrap(viz.WRAP_S,viz.REPEAT)
		tex.wrap(viz.WRAP_T,viz.CLAMP_TO_EDGE)
		tex.anisotropy(8)
		
		texUniform = viz.addUniformInt('tex',0)
		shader = viz.addShader(frag=frag)
		shader.attach(texUniform)
		
		#Initialize remove list
		self.removeList = []
		self.removeList.append(tex)
		self.removeList.append(shader)
		self.removeList.append(texUniform)
		
		self.shader = shader
		self.tex = tex
		
	def apply(self,node):
		node.apply(self.shader)
		node.texture(self.tex)
		node.enable(viz.CLAMP_COLOR)
		
	def remove(self):
		for x in self.removeList:
			x.remove()
		del self.removeList[:]
