<script setup lang="ts">
defineProps<{
  nodes: Array<{
    id: string
    label: string
    children?: Array<{ id: string; label: string }>
  }>
}>()
</script>

<template>
  <el-tree
    :data="nodes.map((node) => ({
      label: node.label,
      children: node.children?.map((child) => ({ label: child.label })),
    }))"
    default-expand-all
  />
</template>
