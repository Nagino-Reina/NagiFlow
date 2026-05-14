/**
 * stores/characters.js
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { charactersApi } from '@/api'

export const useCharactersStore = defineStore('characters', () => {
  const list    = ref([])
  const current = ref(null)
  const loading = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await charactersApi.list(params)
      list.value = data
    } finally { loading.value = false }
  }

  async function fetchOne(id) {
    loading.value = true
    try {
      const { data } = await charactersApi.get(id)
      current.value = data
      return data
    } finally { loading.value = false }
  }

  async function create(payload) {
    const { data } = await charactersApi.create(payload)
    list.value.unshift(data)
    return data
  }

  async function update(id, payload) {
    const { data } = await charactersApi.update(id, payload)
    const idx = list.value.findIndex(c => c.id === id)
    if (idx !== -1) list.value[idx] = data
    if (current.value?.id === id) current.value = data
    return data
  }

  async function remove(id) {
    await charactersApi.delete(id)
    list.value = list.value.filter(c => c.id !== id)
    if (current.value?.id === id) current.value = null
  }

  return { list, current, loading, fetchList, fetchOne, create, update, remove }
})