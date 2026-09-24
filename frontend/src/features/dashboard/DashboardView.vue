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
    <header class="masthead">
      <img
        alt="Studio monogram"
        class="brand-mark"
        src="/brand/logo.jpg"
      >
      <div>
        <small class="eyebrow">Cork City · Ireland</small>
        <h1>Studio operations</h1>
        <p>Internal management system</p>
      </div>
    </header>

    <section class="panel">
      <h2>System status</h2>
      <div class="status-grid">
        <article class="status-card">
          <span class="label">Interface</span>
          <strong class="tone-positive">running</strong>
        </article>
        <article class="status-card">
          <span class="label">API</span>
          <strong
            v-if="!status"
            class="tone-muted"
          >checking…</strong>
          <strong
            v-else
            :class="status.api === 'reachable' ? 'tone-positive' : 'tone-danger'"
          >
            {{ status.api }}
          </strong>
        </article>
        <article class="status-card">
          <span class="label">Database</span>
          <strong
            v-if="!status"
            class="tone-muted"
          >checking…</strong>
          <strong
            v-else
            :class="status.database === 'reachable' ? 'tone-positive' : 'tone-danger'"
          >
            {{ status.database }}
          </strong>
        </article>
      </div>
      <p class="footnote">
        Sprint 01 — technical foundation.
      </p>
    </section>
  </main>
</template>

<style scoped>
.shell {
  min-height: var(--viewport-height);
  display: grid;
  align-content: start;
  gap: var(--space-8);
  padding-bottom: var(--space-12);
}

.masthead {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-10) var(--space-page) var(--space-12);
  border-bottom-left-radius: var(--radius-xl);
  border-bottom-right-radius: var(--radius-xl);
  background: var(--color-ink);
  color: var(--color-on-dark);
}

.brand-mark {
  width: var(--brand-mark-size);
  height: var(--brand-mark-size);
  flex: none;
  object-fit: contain;
  border-radius: var(--radius-sm);
  background: var(--color-black);
  box-shadow: var(--shadow-gold);
}

.eyebrow {
  display: block;
  color: var(--color-gold);
  font-size: var(--text-label-3);
  font-weight: var(--weight-medium);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.masthead h1 {
  margin-top: var(--space-2);
}

.masthead p {
  margin-top: var(--space-1);
  color: var(--color-on-dark-muted);
  font-size: var(--text-label-3);
}

.panel {
  width: min(100%, var(--content-measure));
  margin-inline: var(--space-page);
  display: grid;
  gap: var(--space-5);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: var(--space-4);
}

.status-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.label {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.status-card strong {
  font-size: var(--text-heading-3);
  font-weight: var(--weight-medium);
}

.tone-positive {
  color: var(--color-positive);
}

.tone-danger {
  color: var(--color-danger);
}

.tone-muted {
  color: var(--color-muted);
}

.footnote {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

@media (max-width: 40rem) {
  .masthead {
    flex-direction: column;
    align-items: flex-start;
    padding-top: var(--space-8);
  }
}
</style>
