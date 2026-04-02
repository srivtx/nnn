<script setup lang="ts">
import { Renderer, Program, Mesh, Triangle } from 'ogl';
import { onMounted, onUnmounted, useTemplateRef } from 'vue';

const containerRef = useTemplateRef('containerRef');

const vertexShader = `#version 300 es
in vec2 position;
in vec2 uv;
out vec2 vUv;
void main() {
    vUv = uv;
    gl_Position = vec4(position, 0.0, 1.0);
}
`;

const fragmentShader = `#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2 uResolution;
uniform float uTime;

#define PI 3.14159265359
#define PETALS 12.0

mat2 rot2(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

// Complex folded petal logic mimicking the 3D reference
float layeredFlower(vec2 p) {
    float r = length(p);
    float a = atan(p.y, p.x);

    float f = 0.0;
    
    // 6 dense layers from back to front
    for (float i = 0.0; i < 6.0; i++) {
        // Offset rotation for each layer
        float aOffset = a + i * (PI / PETALS) * 0.5;
        
        // Base petal wave
        float w = cos(aOffset * PETALS);
        
        // Sharpen and shape the petals (pinching the tips)
        // A standard triangle wave produces sharp edges
        float shape = 1.0 - abs(fract(aOffset * PETALS / (2.0 * PI) + 0.5) * 2.0 - 1.0);
        shape = pow(shape, 1.5) * 0.8 + 0.2; // Spiky
        
        // Decrease scale for inner layers
        float layerScale = 1.0 - (i * 0.15);
        
        float petalRadius = shape * layerScale;
        
        // Calculate contribution of this layer based on radius
        // The edge of the petal gives a distinct shape
        float edge = smoothstep(0.02, 0.0, r - petalRadius);
        
        // Combine by taking the max layer presence (union)
        // To give it 3D depth, we'll store the 'height' of the petal
        float height = edge * layerScale * (1.0 - pow(r/petalRadius, 2.0));
        f = max(f, height);
    }
    
    return f;
}

void main() {
    // Normalize coordinates to [-1, 1] accounting for aspect ratio
    vec2 uv = (gl_FragCoord.xy - 0.5 * uResolution.xy) / min(uResolution.x, uResolution.y);
    
    // Scale the flower out so it has plenty of padding and NEVER hits the box edges
    uv *= 1.8;
    
    // Rotate the whole system slowly
    uv = rot2(uTime * 0.1) * uv;
    
    float r = length(uv);
    float a = atan(uv.y, uv.x);

    // Build the flower shape
    // Instead of a simple 2D union, we use a loop to accumulate layers back-to-front
    // which allows proper shadowing.
    
    vec3 colGreen = vec3(0.51, 0.96, 0.44); // Acid green
    vec3 colPink = vec3(0.9, 0.4, 0.85); // Soft pink
    vec3 colPurple = vec3(0.6, 0.2, 0.9); // Deep magenta/purple
    vec3 colBlue = vec3(0.2, 0.3, 0.8); // Core blue
    
    // Initialize color and alpha
    vec3 color = vec3(0.0);
    float alpha = 0.0;
    
    int numLayers = 10;
    for (int i = 0; i < numLayers; i++) {
        float fi = float(i);
        float layerRel = fi / float(numLayers); // 0.0 to 1.0 (back to front)
        
        // Radius scale for this layer
        float scale = 0.9 - layerRel * 0.6; 
        
        // Rotation offset
        float rot = layerRel * PI * 0.25 - uTime * 0.05 * (layerRel + 1.0);
        
        vec2 p = rot2(rot) * uv / scale;
        float pr = length(p);
        float pa = atan(p.y, p.x);
        
        // Base sine wave for petals (12 petals)
        float wave = cos(pa * 12.0);
        
        // Sharpen the wave into individual distinct petals
        float petal = pow(wave * 0.5 + 0.5, 2.0);
        
        // Define the outer boundary of the petal layer
        float boundary = 0.4 + 0.6 * petal;
        
        // If current radius is within this petal layer
        if (pr < boundary) {
            // Distance from edge of the petal
            float edgeDist = boundary - pr;
            
            // Map color purely based on global radius 'r' so the gradient spans the whole flower
            vec3 layerCol = mix(colBlue, colPurple, smoothstep(0.0, 0.15, r));
            layerCol = mix(layerCol, colPink, smoothstep(0.15, 0.3, r));
            layerCol = mix(layerCol, colGreen, smoothstep(0.3, 0.55, r));
            
            // Shade the base of the petal (closer to center) darker to create 3D overlap effect
            float selfShadow = smoothstep(0.0, boundary * 0.5, pr);
            
            // Add a tiny highlight to the very edge
            float edgeHighlight = smoothstep(0.0, 0.05, edgeDist) * smoothstep(0.1, 0.05, edgeDist);
            
            // Subsurface scattering fake (glow at edge of overlapping layer)
            float sss = exp(-edgeDist * 10.0) * 0.5;
            
            // Combine shading
            layerCol *= 0.5 + 0.5 * selfShadow;
            layerCol += colPink * sss;
            layerCol += vec3(1.0) * edgeHighlight * 0.2;
            
            // Anti-alias the edge
            float aa = smoothstep(-0.01, 0.01, edgeDist);
            
            // Under compositing (since we build back to front, we overwrite, representing opaque objects)
            // But we use the AA to softly blend
            color = mix(color, layerCol, aa);
            alpha = mix(alpha, 1.0, aa);
        }
    }
    
    // Darken overall image toward the edges
    color *= smoothstep(0.65, 0.3, r);
    
    // Optional glowing center core
    float core = exp(-r * 30.0);
    color += colGreen * core * 0.5;

    // Force absolute transparency at the rim of the canvas to eliminate any boxy edges
    // The canvas goes from roughly -1.8 to 1.8 because we scaled uv by 1.8
    float radialEdgeFade = smoothstep(1.3, 1.0, length(uv));
    alpha *= radialEdgeFade;
    
    // For alpha rendering on DOM, multiplying color by alpha usually looks cleaner
    fragColor = vec4(color * alpha, alpha);
}
`;

let raf = 0;

onMounted(() => {
  const container = containerRef.value;
  if (!container) return;

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const renderer = new Renderer({ dpr, alpha: true, antialias: true, premultipliedAlpha: false });
  const gl = renderer.gl;
  gl.canvas.style.position = 'absolute';
  gl.canvas.style.inset = '0';
  gl.canvas.style.width = '100%';
  gl.canvas.style.height = '100%';
  container.appendChild(gl.canvas);

  const program = new Program(gl, {
    vertex: vertexShader,
    fragment: fragmentShader,
    uniforms: {
      uResolution: { value: [1, 1] },
      uTime: { value: 0 },
    },
    transparent: true
  });

  const geometry = new Triangle(gl);
  const mesh = new Mesh(gl, { geometry, program });

  const resize = () => {
    const w = container.clientWidth || 1;
    const h = container.clientHeight || 1;
    renderer.setSize(w, h);
    program.uniforms.uResolution.value = [gl.drawingBufferWidth, gl.drawingBufferHeight];
  };

  const observer = new ResizeObserver(resize);
  observer.observe(container);

  let lastTime = performance.now();
  let time = 0;

  const update = (now: number) => {
    const dt = (now - lastTime) * 0.001;
    lastTime = now;
    time += dt;

    program.uniforms.uTime.value = time;
    renderer.render({ scene: mesh });
    raf = requestAnimationFrame(update);
  };
  raf = requestAnimationFrame(update);

  onUnmounted(() => {
    cancelAnimationFrame(raf);
    observer.disconnect();
    try { container.removeChild(gl.canvas); } catch (e) {}
  });
});
</script>

<template>
  <div ref="containerRef" class="w-full h-full pointer-events-none drop-shadow-2xl opacity-90" />
</template>
