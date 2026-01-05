import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { GoogleGenerativeAI } from "https://esm.sh/@google/generative-ai@0.12.0"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

Deno.serve(async (req) => {
  // 1. Обработка Preflight (OPTIONS)
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Проверка ключа API перед всем остальным
    const apiKey = Deno.env.get('GEMINI_API_KEY')
    if (!apiKey) {
      throw new Error('GEMINI_API_KEY is not set on server')
    }

    // Получаем тело запроса
    // Добавляем проверку на пустой body, чтобы избежать краша
    let body;
    try {
        body = await req.json()
    } catch (e) {
        throw new Error('Invalid request body')
    }

    const { assistantType, input } = body

    const genAI = new GoogleGenerativeAI(apiKey)
    const model = genAI.getGenerativeModel({ model: "gemini-pro" })

    let prompt = ''

    // Логика формирования промпта
    if (assistantType === 'task_decomposer') {
        const data = typeof input === 'string' ? JSON.parse(input) : input;
        prompt = `
        Act as a Senior Project Manager. Decompose this task into 3-5 subtasks.
        Parent Task: "${data.title}"
        Description: "${data.description}"

        Return ONLY valid JSON array. Do not use Markdown formatting. Example:
        [
          {"title": "Research API", "description": "Read documentation", "estimated_hours": 2},
          {"title": "Implement Schema", "description": "Create DB tables", "estimated_hours": 4}
        ]
        `
    } else if (assistantType === 'predictive_estimator') {
         const data = typeof input === 'string' ? JSON.parse(input) : input;
         prompt = `Estimate hours for task: "${data.title}". Return valid JSON: {"estimated_hours": 5.5}`
    } else {
        // Fallback for chat
        prompt = `Context: ${input}. Answer briefly in Russian language.`
    }

    const result = await model.generateContent(prompt)
    const response = await result.response
    const text = response.text()

    const cleanText = text.replace(/```json/g, '').replace(/```/g, '').trim();

    return new Response(
      JSON.stringify({ response: cleanText }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )

  } catch (error) {
    console.error("Function error:", error.message)
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400
      }
    )
  }
})
