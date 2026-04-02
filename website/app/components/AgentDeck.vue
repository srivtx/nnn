<template>
  <div class="w-full h-full">
    <!-- Desktop: Interactive CardSwap -->
    <div class="hidden md:block w-full h-full">
      <CardSwap 
        :width="440"
        :height="280"
        :card-distance="32"
        :vertical-distance="36"
        :delay="3500"
        :skew-amount="2"
        easing="elastic"
        :pause-on-hover="true"
      >
        <template v-for="(agent, i) in agents" :key="i" #[`card-${i}`]>
          <div class="w-full h-full p-7 bg-[#0f0f12] border border-white/[0.06] rounded-2xl flex flex-col shadow-[0_20px_60px_rgba(0,0,0,0.8)] relative overflow-hidden transition-colors hover:border-white/[0.1]">
            <div class="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-7 h-7 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-white/60 text-[12px]" :class="agent.iconClass">
                  <span v-if="agent.textIcon" class="font-mono leading-none">{{ agent.textIcon }}</span>
                  <component v-else :is="agent.icon" />
                </div>
                <span class="text-[18px] font-semibold tracking-[-0.02em] text-white/85">{{ agent.name }}</span>
              </div>
              <span class="text-[10px] font-mono text-white/20">{{ String(i + 1).padStart(2, '0') }}</span>
            </div>
            <p class="text-[13px] text-white/35 leading-relaxed font-normal">{{ agent.desc }}</p>
          </div>
        </template>
      </CardSwap>
    </div>

    <!-- Mobile: Clean stacked cards -->
    <div class="md:hidden flex flex-col gap-2">
      <div 
        v-for="(agent, i) in agents" 
        :key="'m-' + i"
        class="flex items-start gap-3 p-4 bg-white/[0.02] border border-white/[0.04] rounded-xl"
      >
        <div class="w-7 h-7 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center shrink-0 text-white/50 text-[11px]" :class="agent.iconClass">
          <span v-if="agent.textIcon" class="font-mono leading-none">{{ agent.textIcon }}</span>
          <component v-else :is="agent.icon" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1">
            <span class="text-[14px] font-semibold tracking-tight text-white/80">{{ agent.name }}</span>
            <span class="text-[10px] font-mono text-white/15">{{ String(i + 1).padStart(2, '0') }}</span>
          </div>
          <p class="text-[12px] text-white/30 leading-relaxed">{{ agent.desc }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { h } from 'vue';
import CardSwap from './CardSwap.vue';

const StarIcon = () => h('svg', { viewBox: '0 0 24 24', class: 'w-3.5 h-3.5 fill-current' }, [
  h('path', { d: 'M12 0 C12 6.6 17.4 12 24 12 C17.4 12 12 17.4 12 24 C12 17.4 6.6 12 0 12 C6.6 12 12 6.6 12 0 Z' })
]);

const CrossIcon = () => h('svg', { viewBox: '0 0 24 24', class: 'w-3 h-3 fill-current', stroke: 'currentColor', 'stroke-width': '1.5' }, [
  h('path', { d: 'M12 2L12 22M2 12L22 12M19.07 4.93L4.93 19.07M19.07 19.07L4.93 4.93' })
]);

const SearchIcon = () => h('svg', { class: 'w-3.5 h-3.5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' })
]);

const GlobeIcon = () => h('svg', { class: 'w-3.5 h-3.5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })
]);

const agents = [
  { name: 'Architect', desc: 'Designs system structure and writes step-by-step execution plans to guarantee structural integrity before code is written.', icon: StarIcon, iconClass: '' },
  { name: 'Developer', desc: 'Reads architectural plans and writes working code using precise, surgical line-by-line workspace edit APIs.', textIcon: '{ }', iconClass: '' },
  { name: 'BugFixer', desc: 'Executes code securely, captures tracebacks, and iterates the codebase until the runtime operates flawlessly.', icon: CrossIcon, iconClass: '' },
  { name: 'Researcher', desc: 'Analyzes your workspace architecture to ensure implementation matches your established design patterns.', icon: SearchIcon, iconClass: '' },
  { name: 'WebSearcher', desc: 'Retrieves real-time documentation from the internet to handle the latest API and framework updates.', icon: GlobeIcon, iconClass: '' },
];
</script>
