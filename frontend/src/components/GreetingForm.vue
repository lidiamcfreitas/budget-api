<template>
<div class="greeting-form">
    <el-form @submit.prevent="submitName">
    <el-input
        v-model="name"
        placeholder="Enter your name"
        :disabled="isLoading"
        class="name-input"
    />
    <el-button
        type="primary"
        @click="submitName"
        :loading="isLoading"
        class="submit-button"
    >
        Submit
    </el-button>
    </el-form>

    <div v-if="greeting" class="greeting-response">
    {{ greeting }}
    </div>

    <el-alert
    v-if="error"
    :title="error"
    type="error"
    show-icon
    class="error-message"
    />
</div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import axios from 'axios'
import { ElForm, ElInput, ElButton, ElAlert } from 'element-plus'

export default defineComponent({
name: 'GreetingForm',
components: {
    ElForm,
    ElInput,
    ElButton,
    ElAlert
},
setup() {
    const name = ref('')
    const greeting = ref('')
    const error = ref('')
    const isLoading = ref(false)

    const submitName = async () => {
    if (!name.value.trim()) {
        error.value = 'Please enter a name'
        return
    }

    error.value = ''
    isLoading.value = true

    try {
        const response = await axios.post('http://127.0.0.1:8000/greet', {
        name: name.value.trim()
        })
        greeting.value = response.data
        name.value = ''
    } catch (err) {
        error.value = err instanceof Error 
        ? err.message 
        : 'An error occurred while fetching the greeting'
    } finally {
        isLoading.value = false
    }
    }

    return {
    name,
    greeting,
    error,
    isLoading,
    submitName
    }
}
})
</script>

<style scoped>
.greeting-form {
max-width: 400px;
margin: 0 auto;
padding: 20px;
}

.name-input {
margin-bottom: 16px;
}

.submit-button {
width: 100%;
}

.greeting-response {
margin-top: 20px;
padding: 16px;
background-color: #f0f9eb;
border-radius: 4px;
text-align: center;
}

.error-message {
margin-top: 16px;
}
</style>

