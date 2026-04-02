<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, useTemplateRef } from 'vue';
import { gsap } from 'gsap';

interface GridMotionProps {
  items?: string[];
  gradientColor?: string;
}

const props = withDefaults(defineProps<GridMotionProps>(), {
  items: () => [],
  gradientColor: '#222222'
});

const gridRef = useTemplateRef<HTMLElement>('gridRef');
const rowRefs = ref<HTMLElement[]>([]);
const mouseX = ref(0); // set in onMounted (SSR-safe)

const TOTAL_ITEMS = 150;
const ITEMS_PER_ROW = 15;
const ROW_COUNT = 10;

const combinedItems = computed<string[]>(() => {
  if (props.items.length === 0) return Array(TOTAL_ITEMS).fill('');
  return Array.from({ length: TOTAL_ITEMS }, (_, i) => props.items[i % props.items.length] ?? '');
});

function isImage(item: string) {
  return item.startsWith('http');
}

function isTag(item: string) {
  return item.startsWith('<') && item.endsWith('>');
}

function getRowItems(rowIndex: number): string[] {
  const start = (rowIndex - 1) * ITEMS_PER_ROW;
  return combinedItems.value.slice(start, start + ITEMS_PER_ROW);
}

onMounted(() => {
  mouseX.value = window.innerWidth / 2;
  gsap.ticker.lagSmoothing(0);

  const handleMouseMove = (e: MouseEvent) => {
    mouseX.value = e.clientX;
  };

  const inertiaFactors = [0.6, 0.4, 0.3, 0.2];
  const updateMotion = () => {
    const maxMoveAmount = 300;
    const baseDuration = 0.8;
    rowRefs.value.forEach((row, index) => {
      const direction = index % 2 === 0 ? 1 : -1;
      const moveAmount = ((mouseX.value / window.innerWidth) * maxMoveAmount - maxMoveAmount / 2) * direction;
      gsap.to(row, {
        x: moveAmount,
        duration: baseDuration + (inertiaFactors[index % inertiaFactors.length] ?? 0.2),
        ease: 'power3.out',
        overwrite: 'auto'
      });
    });
  };

  const removeAnimation = gsap.ticker.add(updateMotion);
  window.addEventListener('mousemove', handleMouseMove);

  onBeforeUnmount(() => {
    window.removeEventListener('mousemove', handleMouseMove);
    removeAnimation();
  });
});
</script>

<template>
  <div ref="gridRef" class="w-full h-full overflow-hidden">
    <section
      class="relative flex justify-center items-center w-full h-screen overflow-hidden"
      :style="{
        background: `radial-gradient(circle, ${gradientColor} 0%, #050505 100%)`,
        backgroundPosition: 'center'
      }"
    >
      <div class="z-[4] absolute inset-0 pointer-events-none"></div>

      <div class="z-[2] relative flex-none gap-4 grid grid-cols-1 w-[150vw] h-[150vh] rotate-[-15deg] origin-center">
        <div
          v-for="rowIndex in ROW_COUNT"
          :key="rowIndex"
          class="gap-4 flex"
          :style="{ willChange: 'transform, filter' }"
          ref="rowRefs"
        >
          <div
            v-for="(item, itemIndex) in getRowItems(rowIndex)"
            :key="itemIndex"
            class="relative h-[250px] min-w-[300px] flex-shrink-0"
            v-show="item.length > 0"
          >
            <div class="relative flex justify-center items-center bg-[#0a0a0f] border border-white/[0.04] rounded-[10px] w-full h-full overflow-hidden text-[1.5rem] text-white">
              <div
                v-if="isImage(item)"
                class="top-0 left-0 absolute bg-cover bg-center w-full h-full opacity-80"
                :style="{ backgroundImage: `url(${item})` }"
              ></div>
              <div
                v-else-if="isTag(item)"
                class="z-[2] p-4 text-center"
                v-html="item"
              ></div>
              <div v-else class="z-[1] p-4 text-center text-white/50 text-base font-mono">{{ item }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="top-0 left-0 relative w-full h-full pointer-events-none"></div>
    </section>
  </div>
</template>
