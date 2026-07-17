<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const type = computed(() => {
  const value = props.status.toLowerCase()

  if (['running', 'active', 'in_progress'].includes(value)) return 'primary'
  if (['completed', 'finished', 'success', 'healthy'].includes(value)) {
    return 'success'
  }
  if (['failed', 'critical', 'error'].includes(value)) return 'danger'
  if (['pending', 'idle', 'warning'].includes(value)) return 'warning'

  return 'info'
})
</script>

<template>
  <el-tag :type="type" size="small" effect="dark">{{ status }}</el-tag>
</template>
