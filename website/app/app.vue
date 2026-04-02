<template>
  <div class="relative min-h-screen bg-[#050505] text-white antialiased overflow-x-hidden">

    <!-- ══ BACKGROUND aurora blobs (behind everything) ══ -->
    <div class="fixed inset-0 z-0 pointer-events-none">
      <!-- Subtle lighting blobs -->
      <div class="aurora-blob aurora-1"></div>
      <div class="aurora-blob aurora-2"></div>
      <div class="aurora-blob aurora-3"></div>
      <div class="noise-overlay"></div>
    </div>

    <!-- ══ NAV ══ -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-[#050505]/70 backdrop-blur-2xl border-b border-white/[0.1] shadow-[0_10px_30px_-10px_rgba(0,0,0,0.5)]">
      <div class="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <a href="/" class="text-xl text-white/70 hover:text-white transition-colors font-medium" style="font-family: 'Newsreader', serif; font-style: italic;">nnn</a>
        <nav class="hidden md:flex gap-7">
          <a href="#agents" class="text-[13px] text-white/30 hover:text-white/70 transition-colors">Agents</a>
          <a href="#features" class="text-[13px] text-white/30 hover:text-white/70 transition-colors">Features</a>
          <a href="https://github.com/srivtx/nnn" target="_blank" class="text-[13px] text-white/30 hover:text-white/70 transition-colors">GitHub</a>
        </nav>
        <a href="https://github.com/srivtx/nnn" target="_blank" class="glow-button text-[13px] font-medium px-4 py-1.5 rounded-lg">
          Get Started
        </a>
      </div>
    </header>

    <main class="relative z-10">

      <!-- ─── HERO ─── -->
      <section class="relative py-24 sm:py-40 bg-transparent z-10 px-4 sm:px-6 flex flex-col items-center justify-center text-center overflow-hidden">
        
        <!-- Hero-specific spatial grid -->
        <div class="absolute inset-0 z-[-1] pointer-events-none">
          <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px)]" style="background-size: 60px 60px; background-position: center;"></div>
          <!-- Fades the grid to black seamlessly at the bottom so it doesn't bleed into the next sections -->
          <div class="absolute bottom-0 inset-x-0 h-40 bg-gradient-to-t from-[#050505] to-transparent"></div>
        </div>

        <!-- SpatialFlower smoothly scaling behind the hero -->
        <div class="absolute top-[40%] sm:top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[110vw] h-[110vw] sm:w-[550px] sm:h-[550px] md:w-[700px] md:h-[700px] z-0 pointer-events-none drop-shadow-[0_0_80px_rgba(232,121,249,0.2)]">
          <SpatialFlower />
        </div>

        <!-- Overlay to dim the burst so text pops -->
        <div class="absolute inset-0 z-[1] bg-gradient-to-b from-[#050505]/60 via-[#050505]/40 to-[#050505] pointer-events-none"></div>

        <div class="max-w-4xl mx-auto relative z-[2] flex flex-col items-center">
          <!-- Status pill -->
          <div class="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full border border-white/[0.06] bg-white/[0.02] text-[11px] sm:text-[12px] text-white/40 mb-8 sm:mb-12 backdrop-blur-md">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
            </span>
            Now in public beta
          </div>

          <!-- Giant heading -->
          <h1 class="text-[clamp(2.5rem,8vw,7rem)] font-bold tracking-[-0.05em] leading-[0.95] mb-6 sm:mb-8 mx-auto max-w-[90vw]">
            <span class="block shimmer-text">Code that</span>
            <span class="block gradient-text-animated">writes itself.</span>
          </h1>

          <p class="text-[15px] sm:text-[16px] md:text-[18px] text-white/40 max-w-[90vw] sm:max-w-lg mx-auto leading-[1.6] mb-10 sm:mb-14 font-light">
            Five specialized AI agents that design, write, fix, and research code — autonomously — running entirely on your hardware.
          </p>

          <!-- Install command -->
          <div class="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto px-4">
            <div class="relative group w-full sm:w-auto">
              <div class="absolute -inset-[1px] bg-gradient-to-r from-violet-500/30 via-fuchsia-500/30 to-cyan-500/30 rounded-xl opacity-0 group-hover:opacity-100 blur-sm transition-opacity duration-700"></div>
              <div class="relative flex items-center justify-between sm:justify-start gap-3 h-12 px-5 bg-[#0a0a0f] border border-white/[0.08] rounded-xl text-[13px] font-mono group-hover:border-white/[0.12] transition-colors">
                <span class="text-white/20">$</span>
                <span class="text-white/70 select-all">uv tool install nnn-agent</span>
                <button @click="copyInstall" class="text-white/25 hover:text-white/70 transition-colors ml-2" title="Copy">
                  <svg class="w-3.5 h-3.5" :class="copied ? 'text-emerald-400' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path v-if="copied" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /><path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                </button>
              </div>
            </div>
            <a href="#agents" class="text-[13px] text-white/30 hover:text-white/60 transition-colors flex items-center gap-1.5 mt-4 sm:mt-0">
              See how it works
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
            </a>
          </div>
        </div>

        <!-- Floating scroll line -->
        <div class="absolute bottom-10 left-1/2 -translate-x-1/2 z-[2]">
          <div class="w-px h-16 bg-gradient-to-b from-transparent via-white/10 to-transparent animate-pulse"></div>
        </div>
      </section>

      <!-- ─── AGENTS ─── -->
      <section id="agents" class="py-24 md:py-40 px-6 relative">
        <!-- Subtle section divider -->
        <div class="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent"></div>
        <div class="max-w-6xl mx-auto">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 px-2 sm:px-0 mt-20 items-center animate-on-scroll">
            <!-- Text -->
            <div class="md:col-span-1">
              <span class="section-label text-violet-400/60 mb-5 block">// agents</span>
              <h2 class="section-heading mb-6">
                <span class="text-white/90">Five minds.</span><br />
                <span class="text-white/40">One loop.</span>
              </h2>
              <p class="text-[15px] text-white/25 leading-relaxed mb-10 max-w-md">
                Each agent owns a phase of the dev lifecycle — from architecture to deployment. They pass context fluidly through a shared execution loop.
              </p>
              <!-- Agent pills -->
              <div class="flex flex-wrap gap-2">
                <span v-for="(a, i) in agentNames" :key="a"
                  class="agent-pill text-[12px] font-mono px-3 py-1.5 rounded-lg"
                  :style="{ '--delay': i * 0.1 + 's' }">
                  {{ a }}
                </span>
              </div>
            </div>
            <!-- CardSwap -->
            <div class="md:col-span-2 relative h-[380px] sm:h-[420px] pb-32 md:pb-0 flex items-center justify-center mt-10 md:mt-0">
              <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(56,189,248,0.08),transparent_60%)] blur-2xl pointer-events-none"></div>
              <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(167,139,250,0.06),transparent_60%)] blur-2xl pointer-events-none"></div>
              
              <div class="relative w-full max-w-[440px] h-[300px]">
                <AgentDeck />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ─── GRID MOTION SHOWCASE ─── -->
      <section class="relative overflow-hidden mt-20 md:mt-0" style="height: 480px;">
        <!-- Label -->
        <div class="absolute top-8 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
          <div class="flex items-center gap-3">
            <div class="h-px w-12 bg-gradient-to-r from-transparent to-white/20"></div>
            <span class="section-label text-white/20">built for the terminal</span>
            <div class="h-px w-12 bg-gradient-to-l from-transparent to-white/20"></div>
          </div>
        </div>
        <!-- Stronger top + bottom fade for clean blending -->
        <div class="absolute top-0 inset-x-0 h-56 bg-gradient-to-b from-[#050505] via-[#050505]/80 to-transparent z-10 pointer-events-none"></div>
        <div class="absolute bottom-0 inset-x-0 h-56 bg-gradient-to-t from-[#050505] via-[#050505]/80 to-transparent z-10 pointer-events-none"></div>
        <!-- Side fades to soften the clipped edges -->
        <div class="absolute top-0 left-0 w-40 h-full bg-gradient-to-r from-[#050505] to-transparent z-10 pointer-events-none"></div>
        <div class="absolute top-0 right-0 w-40 h-full bg-gradient-to-l from-[#050505] to-transparent z-10 pointer-events-none"></div>
        <GridMotion :items="gridItems" gradientColor="rgba(5,5,5,0.9)" />
      </section>

      <!-- ─── FEATURES ─── -->
      <section id="features" class="pt-20 md:pt-32 pb-28 md:pb-40 px-6 relative">
        <!-- Gradient bridge from GridMotion above — smooth blend -->
        <div class="absolute -top-24 inset-x-0 h-32 bg-gradient-to-b from-transparent to-[#050505] z-0 pointer-events-none"></div>
        <!-- Subtle section divider -->
        <div class="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/[0.04] to-transparent"></div>
        <!-- Glowing orbs behind the grid -->
        <div class="absolute left-0 top-1/3 w-[800px] h-[800px] bg-fuchsia-600/10 rounded-full blur-[120px] pointer-events-none mix-blend-screen opacity-50"></div>
        <div class="absolute right-0 bottom-0 w-[600px] h-[600px] bg-cyan-600/10 rounded-full blur-[100px] pointer-events-none mix-blend-screen opacity-50"></div>

        <div class="max-w-6xl mx-auto relative z-10">
          <div class="text-center mb-20 relative z-10 animate-on-scroll">
            <span class="section-label tracking-widest text-fuchsia-400/60 mb-5 block">// capabilities</span>
            <h2 class="section-heading tracking-tight mb-5 text-white/90">Built different.</h2>
            <p class="text-[16px] text-[#a1a1aa] font-light max-w-md mx-auto leading-relaxed">Not another wrapper. A hardened native runtime with real engineering under the hood.</p>
          </div>

          <!-- Feature bento grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 relative z-10 animate-on-scroll delay-100">
            <div v-for="(f, i) in features" :key="i"
              class="feature-card group relative p-7 rounded-2xl overflow-hidden glassmorphic shadow-2xl transition-all duration-500 hover:-translate-y-1 hover:shadow-cyan-500/10 hover:border-white/10"
              :class="f.span ? 'lg:col-span-2' : ''">
              <!-- Glow line on top -->
              <div class="absolute inset-x-0 top-0 h-px" :class="f.glowClass"></div>
              <!-- Content -->
              <div class="relative z-10" :class="f.span ? 'flex flex-col md:flex-row gap-8 items-start' : ''">
                <div :class="f.span ? 'flex-1' : ''">
                  <div class="flex items-center gap-2 mb-4">
                    <span v-html="f.iconHtml" :class="f.iconColor" class="flex-shrink-0"></span>
                    <span class="section-label tracking-widest text-[10px]" :class="f.labelColor">{{ f.label }}</span>
                  </div>
                  <h3 class="text-[20px] font-medium tracking-tight text-white/90 mb-3 group-hover:text-white transition-colors drop-shadow-md">{{ f.title }}</h3>
                  <p class="text-[15px] font-light text-white/40 leading-[1.7]" :class="f.span ? 'max-w-md' : ''">{{ f.desc }}</p>
                </div>
                <!-- Terminal for the wide card -->
                <div v-if="f.span" class="w-full md:w-[320px] shrink-0 rounded-xl border border-white/[0.06] bg-[#08080b] overflow-hidden mt-4 md:mt-0">
                  <div class="h-8 border-b border-white/[0.04] flex items-center px-3 gap-1.5">
                    <div class="w-2 h-2 rounded-full bg-red-500/30"></div>
                    <div class="w-2 h-2 rounded-full bg-yellow-500/30"></div>
                    <div class="w-2 h-2 rounded-full bg-green-500/30"></div>
                    <span class="text-[9px] text-white/15 font-mono ml-2">terminal</span>
                  </div>
                  <div class="p-4 font-mono text-[11px] leading-[1.9]">
                    <div class="text-white/30"><span class="text-emerald-400/50">❯</span> nnn "add user auth"</div>
                    <div class="text-violet-400/50 mt-1">  → planning...</div>
                    <div class="text-blue-400/50">  → writing code...</div>
                    <div class="text-amber-400/50">  → testing...</div>
                    <div class="text-emerald-400/60 mt-1">  ✓ done · 3 files</div>
                    <div class="text-white/30 mt-1"><span class="text-emerald-400/50">❯</span> <span class="animate-pulse">▊</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ─── CTA ─── -->
      <section class="py-28 md:py-40 px-6 text-center relative overflow-hidden">
        <!-- Subtle top divider -->
        <div class="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/[0.04] to-transparent z-10"></div>
        <!-- Very subtle radial glow — toned down to match the dark aesthetic -->
        <div class="absolute inset-0 z-0">
          <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(139,92,246,0.05)_0%,rgba(139,92,246,0.02)_40%,transparent_65%)]"></div>
        </div>

        <div class="relative z-[2] max-w-2xl mx-auto mt-10 animate-on-scroll">
          <span class="section-label tracking-widest text-violet-400/50 mb-5 block">// get started</span>
          <h2 class="section-heading tracking-tight mb-6 text-white/90 drop-shadow-xl">Ship faster. <span class="gradient-text-animated block sm:inline mt-2 sm:mt-0">Locally.</span></h2>
          <p class="text-[16px] text-[#a1a1aa] font-light leading-relaxed mb-14 max-w-sm mx-auto">
            No API keys. No cloud. No nonsense. One command.
          </p>
          <a href="https://github.com/srivtx/nnn" target="_blank" class="inline-flex items-center gap-3 h-12 px-7 cta-button rounded-xl text-[14px] font-semibold transition-all duration-300 hover:scale-[1.02]">
            <svg class="w-5 h-5 opacity-70" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            Star on GitHub
          </a>
        </div>
      </section>

    </main>

    <!-- ══ FOOTER ══ -->
    <footer class="relative z-10 border-t border-white/[0.03] py-10 px-6 bg-[#050505]">
      <div class="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <span class="text-lg text-white/10" style="font-family: 'Newsreader', serif; font-style: italic;">nnn</span>
        <div class="flex items-center gap-5 text-[11px] text-white/15 font-mono">
          <a href="https://github.com/srivtx/nnn" target="_blank" class="hover:text-white/40 transition-colors">github</a>
          <span>·</span>
          <span>mit</span>
          <span>·</span>
          <span>2026</span>
        </div>
      </div>
    </footer>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useHead } from '#imports';
import AgentDeck from './components/AgentDeck.vue';
import GridMotion from './components/GridMotion.vue';
import SpatialFlower from './components/SpatialFlower.vue';

let observer: IntersectionObserver;

onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target); // only animate once
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

  document.querySelectorAll('.animate-on-scroll').forEach((el) => {
    observer.observe(el);
  });
});

onUnmounted(() => {
  if (observer) observer.disconnect();
});

useHead({
  title: 'nnn — code that writes itself',
  meta: [
    { name: 'description', content: 'Five specialized AI agents that design, write, fix, and research code. Running entirely on your machine.' },
  ]
});

const copied = ref(false);
const copyInstall = async () => {
  try {
    await navigator.clipboard.writeText('uv tool install nnn-agent');
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  } catch (err) { console.error(err); }
};

const agentNames = ['Architect', 'Developer', 'BugFixer', 'Researcher', 'WebSearcher'];

const gridItems = [
  `<div class="glass-card" style="border-top:1px solid rgba(139,92,246,0.3)">
    <div style="font-family:monospace;font-size:10px;color:rgba(167,139,250,0.6);letter-spacing:0.2em;text-transform:uppercase">// agent 01</div>
    <div>
      <div style="font-size:20px;font-weight:600;color:rgba(255,255,255,0.95);letter-spacing:-0.03em;margin-bottom:8px">Architect</div>
      <div style="font-size:13px;font-weight:300;color:rgba(255,255,255,0.4);line-height:1.6">Designs system structure and writes execution plans before code.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="border-top:1px solid rgba(6,182,212,0.3)">
    <div style="font-family:monospace;font-size:10px;color:rgba(34,211,238,0.6);letter-spacing:0.2em;text-transform:uppercase">// agent 02</div>
    <div>
      <div style="font-size:20px;font-weight:600;color:rgba(255,255,255,0.95);letter-spacing:-0.03em;margin-bottom:8px">Developer</div>
      <div style="font-size:13px;font-weight:300;color:rgba(255,255,255,0.4);line-height:1.6">Reads plans and writes working code with surgical line edits.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="border-top:1px solid rgba(239,68,68,0.3)">
    <div style="font-family:monospace;font-size:10px;color:rgba(248,113,113,0.6);letter-spacing:0.2em;text-transform:uppercase">// agent 03</div>
    <div>
      <div style="font-size:20px;font-weight:600;color:rgba(255,255,255,0.95);letter-spacing:-0.03em;margin-bottom:8px">BugFixer</div>
      <div style="font-size:13px;font-weight:300;color:rgba(255,255,255,0.4);line-height:1.6">Captures tracebacks and iterates until the runtime is green.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="border-top:1px solid rgba(234,179,8,0.2)">
    <div style="font-family:monospace;font-size:10px;color:rgba(250,204,21,0.6);letter-spacing:0.2em;text-transform:uppercase">// agent 04</div>
    <div>
      <div style="font-size:20px;font-weight:600;color:rgba(255,255,255,0.95);letter-spacing:-0.03em;margin-bottom:8px">Researcher</div>
      <div style="font-size:13px;font-weight:300;color:rgba(255,255,255,0.4);line-height:1.6">Analyzes your workspace to match established design patterns.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="border-top:1px solid rgba(52,211,153,0.2)">
    <div style="font-family:monospace;font-size:10px;color:rgba(52,211,153,0.6);letter-spacing:0.2em;text-transform:uppercase">// agent 05</div>
    <div>
      <div style="font-size:20px;font-weight:600;color:rgba(255,255,255,0.95);letter-spacing:-0.03em;margin-bottom:8px">WebSearcher</div>
      <div style="font-size:13px;font-weight:300;color:rgba(255,255,255,0.4);line-height:1.6">Retrieves real-time docs for the latest API and framework updates.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="justify-content:center;align-items:center;gap:8px;">
    <div style="font-family:monospace;font-size:12px;color:rgba(255,255,255,0.2);margin-bottom:4px">$ <span style="color:rgba(167,139,250,0.7)">nnn</span> "add user auth"</div>
    <div style="font-family:monospace;font-size:11px;color:rgba(167,139,250,0.4)">→ planning architecture...</div>
    <div style="font-family:monospace;font-size:11px;color:rgba(6,182,212,0.4)">→ writing code...</div>
    <div style="font-family:monospace;font-size:11px;color:rgba(234,179,8,0.4)">→ running tests...</div>
    <div style="font-family:monospace;font-size:11px;color:rgba(52,211,153,0.6)">✓ done · 3 files changed</div>
  </div>`,

  `<div class="glass-card" style="justify-content:center;align-items:center;text-align:center;gap:10px;">
    <div style="font-size:32px;font-weight:800;color:rgba(255,255,255,0.08);letter-spacing:-0.05em;line-height:1">100%</div>
    <div style="font-size:14px;font-weight:600;color:rgba(52,211,153,0.8)">Local & Private</div>
    <div style="font-size:12px;font-weight:300;color:rgba(255,255,255,0.4);max-width:180px;line-height:1.6">Zero cloud. Zero telemetry. Runs on your own hardware.</div>
  </div>`,

  `<div class="glass-card" style="justify-content:center;align-items:center;text-align:center;gap:10px;">
    <div style="font-size:28px;font-weight:800;color:rgba(255,255,255,0.06);letter-spacing:-0.05em;line-height:1">5</div>
    <div style="font-size:13px;font-weight:600;color:rgba(167,139,250,0.6)">Specialist Agents</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.2);max-width:180px;line-height:1.5">Each agent owns a distinct phase of the dev lifecycle.</div>
  </div>`,

  `<div class="glass-card" style="justify-content:space-between;border-top:1px solid rgba(139,92,246,0.12)">
    <div style="font-family:monospace;font-size:10px;color:rgba(167,139,250,0.4);letter-spacing:0.15em;text-transform:uppercase">Precision</div>
    <div>
      <div style="font-size:15px;font-weight:600;color:rgba(255,255,255,0.75);margin-bottom:6px">Surgical code edits</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.4);line-height:1.6">Line-by-line patches — never overwrites your files.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="justify-content:space-between;border-top:1px solid rgba(6,182,212,0.12)">
    <div style="font-family:monospace;font-size:10px;color:rgba(6,182,212,0.4);letter-spacing:0.15em;text-transform:uppercase">Recovery</div>
    <div>
      <div style="font-size:15px;font-weight:600;color:rgba(255,255,255,0.75);margin-bottom:6px">Self-healing loop</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.4);line-height:1.6">BugFixer captures tracebacks and patches until green.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="justify-content:space-between;border-top:1px solid rgba(52,211,153,0.12)">
    <div style="font-family:monospace;font-size:10px;color:rgba(52,211,153,0.4);letter-spacing:0.15em;text-transform:uppercase">Privacy</div>
    <div>
      <div style="font-size:15px;font-weight:600;color:rgba(255,255,255,0.75);margin-bottom:6px">Zero cloud exposure</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.4);line-height:1.6">Your code never touches external servers.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="justify-content:space-between;border-top:1px solid rgba(234,179,8,0.12)">
    <div style="font-family:monospace;font-size:10px;color:rgba(234,179,8,0.4);letter-spacing:0.15em;text-transform:uppercase">Context</div>
    <div>
      <div style="font-size:15px;font-weight:600;color:rgba(255,255,255,0.75);margin-bottom:6px">Deep workspace awareness</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.4);line-height:1.6">Every change is context-aligned with your codebase.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="justify-content:center;align-items:center;text-align:center;gap:8px;">
    <div style="font-family:monospace;font-size:20px;font-weight:700;color:rgba(167,139,250,0.5);letter-spacing:0.05em">>_</div>
    <div style="font-size:13px;font-weight:600;color:rgba(255,255,255,0.5)">Native Terminal</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.4);max-width:180px;line-height:1.5">Autonomous shell access. Installs deps, runs tests.</div>
  </div>`,

  `<div class="glass-card" style="justify-content:center;align-items:center;text-align:center;gap:6px;">
    <div style="font-family:monospace;font-size:11px;color:rgba(255,255,255,0.15)">install with</div>
    <div style="font-family:monospace;font-size:13px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);padding:8px 14px;border-radius:8px;color:rgba(167,139,250,0.7)">uv tool install nnn-agent</div>
    <div style="font-family:monospace;font-size:10px;color:rgba(52,211,153,0.35);margin-top:4px">↑ copy & run</div>
  </div>`,

  `<div class="glass-card" style="justify-content:center;align-items:center;text-align:center;gap:8px;">
    <div style="font-size:11px;color:rgba(255,255,255,0.12);font-family:monospace;text-transform:uppercase;letter-spacing:0.1em">One loop</div>
    <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;justify-content:center">
      <span style="font-size:10px;font-family:monospace;padding:4px 8px;border-radius:6px;background:rgba(109,40,217,0.1);border:1px solid rgba(109,40,217,0.15);color:rgba(167,139,250,0.6)">Architect</span>
      <span style="color:rgba(255,255,255,0.1);font-size:10px">→</span>
      <span style="font-size:10px;font-family:monospace;padding:4px 8px;border-radius:6px;background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.12);color:rgba(34,211,238,0.6)">Developer</span>
      <span style="color:rgba(255,255,255,0.1);font-size:10px">→</span>
      <span style="font-size:10px;font-family:monospace;padding:4px 8px;border-radius:6px;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.12);color:rgba(248,113,113,0.6)">BugFixer</span>
    </div>
    <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;justify-content:center">
      <span style="font-size:10px;font-family:monospace;padding:4px 8px;border-radius:6px;background:rgba(234,179,8,0.08);border:1px solid rgba(234,179,8,0.12);color:rgba(250,204,21,0.6)">Researcher</span>
      <span style="color:rgba(255,255,255,0.1);font-size:10px">→</span>
      <span style="font-size:10px;font-family:monospace;padding:4px 8px;border-radius:6px;background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.12);color:rgba(52,211,153,0.6)">WebSearcher</span>
    </div>
  </div>`,

  `<div class="glass-card" style="justify-content:space-between;border-top:1px solid rgba(244,114,182,0.1)">
    <div style="font-family:monospace;font-size:10px;color:rgba(244,114,182,0.4);letter-spacing:0.15em;text-transform:uppercase">Runtime</div>
    <div style="font-family:monospace;font-size:11px;color:rgba(255,255,255,0.4);line-height:2">
      <div><span style="color:rgba(52,211,153,0.5)">❯</span> nnn "refactor API layer"</div>
      <div style="color:rgba(167,139,250,0.4)">  planning... ✓</div>
      <div style="color:rgba(6,182,212,0.4)">  writing code... ✓</div>
      <div style="color:rgba(52,211,153,0.5)">  ✓ 7 files · tests green</div>
    </div>
  </div>`,

  `<div class="glass-card" style="justify-content:center;align-items:center;text-align:center;gap:8px;">
    <div style="font-size:11px;color:rgba(255,255,255,0.12);font-family:monospace">built for</div>
    <div style="font-size:20px;font-weight:700;color:rgba(255,255,255,0.6);letter-spacing:-0.04em">developers</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.4);max-width:160px;line-height:1.5">who move fast and ship without permission.</div>
  </div>`,

  `<div class="glass-card" style="justify-content:space-between;border-top:1px solid rgba(167,139,250,0.1)">
    <div style="font-family:monospace;font-size:10px;color:rgba(167,139,250,0.4);letter-spacing:0.15em;text-transform:uppercase">Open Source</div>
    <div>
      <div style="font-size:15px;font-weight:600;color:rgba(255,255,255,0.75);margin-bottom:6px">MIT Licensed</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.4);line-height:1.6">Free forever. Fork it, extend it, make it yours.</div>
    </div>
  </div>`,

  `<div class="glass-card" style="justify-content:center;align-items:center;text-align:center;gap:10px;">
    <div style="font-size:28px;font-weight:800;color:rgba(255,255,255,0.05);letter-spacing:-0.05em">∞</div>
    <div style="font-size:13px;font-weight:600;color:rgba(244,114,182,0.5)">Execution Loops</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.4);max-width:180px;line-height:1.5">Agents retry until the task is complete.</div>
  </div>`,

  `<div class="glass-card" style="justify-content:space-between;border-top:1px solid rgba(6,182,212,0.1)">
    <div style="font-family:monospace;font-size:10px;color:rgba(6,182,212,0.4);letter-spacing:0.15em;text-transform:uppercase">No cloud</div>
    <div style="display:flex;flex-direction:column;gap:6px">
      <div style="display:flex;align-items:center;gap:8px"><span style="width:5px;height:5px;border-radius:50%;background:rgba(52,211,153,0.5);flex-shrink:0"></span><span style="font-size:11px;color:rgba(255,255,255,0.4)">No API keys required</span></div>
      <div style="display:flex;align-items:center;gap:8px"><span style="width:5px;height:5px;border-radius:50%;background:rgba(52,211,153,0.5);flex-shrink:0"></span><span style="font-size:11px;color:rgba(255,255,255,0.4)">No telemetry or tracking</span></div>
      <div style="display:flex;align-items:center;gap:8px"><span style="width:5px;height:5px;border-radius:50%;background:rgba(52,211,153,0.5);flex-shrink:0"></span><span style="font-size:11px;color:rgba(255,255,255,0.4)">Works fully offline</span></div>
      <div style="display:flex;align-items:center;gap:8px"><span style="width:5px;height:5px;border-radius:50%;background:rgba(52,211,153,0.5);flex-shrink:0"></span><span style="font-size:11px;color:rgba(255,255,255,0.4)">LM Studio compatible</span></div>
    </div>
  </div>`,
];

const features = [
  {
    label: 'Precision',
    labelColor: 'text-violet-400/60',
    iconColor: 'text-violet-400/80',
    iconHtml: '<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-width="1.2" d="M12 3v18m9-9H3" /></svg>',
    glowClass: 'bg-gradient-to-r from-violet-500/40 via-violet-500/10 to-transparent',
    title: 'Surgical code edits',
    desc: 'Line-by-line patches. Never overwrites your files — injects changes with surgical precision.',
  },
  {
    label: 'Recovery',
    labelColor: 'text-blue-400/60',
    iconColor: 'text-blue-400/80',
    iconHtml: '<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-width="1.2" d="M4 12a8 8 0 018-8v0a8 8 0 018 8v0m-16 0A8 8 0 0012 20v0a8 8 0 008-8v0" /></svg>',
    glowClass: 'bg-gradient-to-r from-blue-500/40 via-blue-500/10 to-transparent',
    title: 'Self-healing loop',
    desc: 'Errors trigger auto-recovery. The BugFixer agent captures tracebacks and patches until green.',
  },
  {
    label: 'Privacy',
    labelColor: 'text-emerald-400/60',
    iconColor: 'text-emerald-400/80',
    iconHtml: '<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><rect stroke-width="1.2" x="7" y="10" width="10" height="10" rx="1.5" /><path stroke-width="1.2" d="M9 10V7a3 3 0 016 0v3" /></svg>',
    glowClass: 'bg-gradient-to-r from-emerald-500/40 via-emerald-500/10 to-transparent',
    title: 'Zero cloud exposure',
    desc: 'It runs locally. Your API keys and codebase never leave your machine natively.',
  },
  {
    label: 'Context',
    labelColor: 'text-cyan-400/60',
    iconColor: 'text-cyan-400/80',
    iconHtml: '<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><rect stroke-width="1.2" x="3" y="3" width="7" height="7" /><rect stroke-width="1.2" x="14" y="3" width="7" height="7" /><rect stroke-width="1.2" x="14" y="14" width="7" height="7" /><rect stroke-width="1.2" x="3" y="14" width="7" height="7" /></svg>',
    glowClass: 'bg-gradient-to-r from-cyan-500/40 via-cyan-500/10 to-transparent',
    title: 'Deep workspace awareness',
    desc: 'The Researcher agent maps your exact project architecture before a single line is written.'
  },
  {
    label: 'Runtime',
    labelColor: 'text-fuchsia-400/60',
    iconColor: 'text-fuchsia-400/80',
    iconHtml: '<span class="font-mono font-bold text-sm">>_</span>',
    glowClass: 'bg-gradient-to-r from-fuchsia-500/40 via-fuchsia-500/10 to-transparent',
    title: 'Native terminal execution',
    desc: 'Full autonomous shell access. Installs deps, runs tests, validates everything.',
    span: true
  }
];
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Newsreader:ital,opsz,wght@1,6..72,500&display=swap');

body {
  font-family: 'Inter', -apple-system, sans-serif;
  background: #050505;
  -webkit-font-smoothing: antialiased;
}

html { scroll-behavior: smooth; }

::selection {
  background: rgba(139, 92, 246, 0.3);
  color: white;
}

/* ═══ UNIFIED SECTION LABELS ═══ */
.section-label {
  font-size: 11px;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

/* ═══ UNIFIED SECTION HEADINGS ═══ */
.section-heading {
  font-size: clamp(1.875rem, 5vw, 3rem);
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1.05;
}

/* ═══ AURORA BLOBS ═══ */
.aurora-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  mix-blend-mode: screen;
  pointer-events: none;
  opacity: 0.7;
}
.aurora-1 {
  width: 600px; height: 600px;
  top: -200px; left: 10%;
  background: radial-gradient(circle, rgba(139,92,246,0.12), transparent 70%);
  animation: float-1 20s ease-in-out infinite;
}
.aurora-2 {
  width: 500px; height: 500px;
  top: 30%; right: 5%;
  background: radial-gradient(circle, rgba(236,72,153,0.08), transparent 70%);
  animation: float-2 25s ease-in-out infinite;
}
.aurora-3 {
  width: 700px; height: 400px;
  bottom: 10%; left: 30%;
  background: radial-gradient(circle, rgba(6,182,212,0.06), transparent 70%);
  animation: float-3 30s ease-in-out infinite;
}

@keyframes float-1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(80px, 40px) scale(1.1); }
  66% { transform: translate(-40px, 80px) scale(0.9); }
}
@keyframes float-2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-60px, -30px) scale(1.15); }
  66% { transform: translate(30px, -60px) scale(0.85); }
}
@keyframes float-3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-100px, -40px) scale(1.1); }
}

/* ═══ NOISE ═══ */
.noise-overlay {
  position: absolute;
  inset: 0;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat;
}

/* ═══ GRADIENT TEXT ═══ */
.gradient-text-animated {
  background: linear-gradient(135deg, #a78bfa, #f472b6, #22d3ee, #a78bfa);
  background-size: 300% 300%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient-shift 6s ease infinite;
}

.shimmer-text {
  color: rgba(255,255,255,0.85);
  background: linear-gradient(110deg, rgba(255,255,255,0) 30%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0) 70%);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  animation: shimmer 4s ease-in-out infinite;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes shimmer {
  0%, 100% { background-position: -200% 0; }
  50% { background-position: 200% 0; }
}

/* ═══ GLOW BUTTON ═══ */
.glow-button {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.7);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.glow-button::before {
  content: '';
  position: absolute;
  inset: -1px;
  background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(236,72,153,0.2), rgba(6,182,212,0.3));
  border-radius: inherit;
  opacity: 0;
  transition: opacity 0.5s ease;
  z-index: -1;
  filter: blur(1px);
}
.glow-button:hover {
  border-color: rgba(255,255,255,0.15);
  color: white;
  box-shadow: 0 0 30px rgba(139,92,246,0.1);
}
.glow-button:hover::before { opacity: 1; }

/* ═══ AGENT PILLS ═══ */
.agent-pill {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.4);
  transition: all 0.4s ease;
  animation: pill-glow 3s ease-in-out infinite;
  animation-delay: var(--delay);
}
.agent-pill:hover {
  border-color: rgba(139,92,246,0.3);
  color: rgba(255,255,255,0.7);
  box-shadow: 0 0 20px rgba(139,92,246,0.08);
}

@keyframes pill-glow {
  0%, 100% { border-color: rgba(255,255,255,0.06); }
  50% { border-color: rgba(139,92,246,0.12); }
}

/* ═══ FEATURE CARDS ═══ */
.glassmorphic {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

/* ═══ SCROLL ANIMATIONS ═══ */
.animate-on-scroll {
  opacity: 0;
  transform: translateY(30px) scale(0.98);
  transition: opacity 1s cubic-bezier(0.16, 1, 0.3, 1), transform 1s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: opacity, transform;
}
.animate-on-scroll.is-visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}
.delay-100 { transition-delay: 150ms; }
.delay-200 { transition-delay: 300ms; }

.feature-card {
  --tw-shadow-color: rgba(6, 182, 212, 0);
  background: radial-gradient(circle at top left, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
  border: 1px solid rgba(255, 255, 255, 0.03);
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.feature-card:hover {
  background: rgba(255,255,255,0.035);
  border-color: rgba(255,255,255,0.07);
  transform: translateY(-2px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.3), 0 0 30px rgba(139,92,246,0.04);
}

/* ═══ CTA BUTTON ═══ */
.cta-button {
  background: linear-gradient(135deg, rgba(139,92,246,0.85), rgba(167,139,250,0.75));
  color: white;
  box-shadow: 0 0 30px rgba(139,92,246,0.15);
  transition: all 0.3s ease;
}
.cta-button:hover {
  box-shadow: 0 0 50px rgba(139,92,246,0.25), 0 0 15px rgba(139,92,246,0.15);
  background: linear-gradient(135deg, rgba(139,92,246,0.95), rgba(167,139,250,0.85));
}
/* Base setup for GridMotion inner cards */
.grid-card-inner {
  width: 100%;
  height: 100%;
  padding: 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: inherit; /* adopts card corner radius */
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 10px 40px -10px rgba(0,0,0,0.5);
}
</style>
