<script setup lang="ts">
import { onMounted, ref } from "vue";

import type { SystemStatus } from "@/shared/api/SystemStatus";
import { SystemStatusClient } from "@/shared/api/SystemStatusClient";

const status = ref<SystemStatus | null>(null);
const client = new SystemStatusClient();

onMounted(async () => {
  status.value = await client.fetch();
});
</script>

<template>
  <main class="shell">
    <header>
      <small>TATTOO STUDIO · CORK CITY</small>
      <h1>Studio operations</h1>
      <p>Internal management system. Foundation sprint.</p>
    </header>

    <section class="status-grid">
      <article class="status-card">
        <span class="label">Interface</span>
        <strong class="tone-positive">running</strong>
      </article>
      <article class="status-card">
        <span class="label">API</span>
        <strong v-if="!status">checking…</strong>
        <strong
          v-else
          :class="status.api === 'reachable' ? 'tone-positive' : 'tone-danger'"
        >
          {{ status.api }}
        </strong>
      </article>
      <article class="status-card">
        <span class="label">Database</span>
        <strong v-if="!status">checking…</strong>
        <strong
          v-else
          :class="status.database === 'reachable' ? 'tone-positive' : 'tone-danger'"
        >
          {{ status.database }}
        </strong>
      </article>
    </section>
  </main>
</template>

<style scoped>
.shell {
  min-height: var(--viewport-height);
  padding: var(--space-page);
  display: grid;
  align-content: start;
  gap: var(--space-8);
}

header small {
  color: var(--color-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  letter-spacing: var(--tracking-wide);
}

header h1 {
  margin-top: var(--space-2);
  font-size: var(--text-xl);
  font-weight: var(--weight-medium);
}

header p {
  margin-top: var(--space-2);
  color: var(--color-muted);
  font-size: var(--text-sm);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: var(--space-4);
}

.status-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-6);
  border: var(--border-thin);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.label {
  color: var(--color-muted);
  font-size: var(--text-sm);
}

.status-card strong {
  font-size: var(--text-lg);
  font-weight: var(--weight-medium);
}

.tone-positive {
  color: var(--color-positive);
}

.tone-danger {
  color: var(--color-danger);
}
</style>
