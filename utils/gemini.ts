import { GoogleGenerativeAI } from "@google/generative-ai";

export async function analyzeVideoContent(apiKey: string, audioFile: File): Promise<any[]> {
  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

  // Convert audio file to base64
  const audioBase64 = await fileToGenerativePart(audioFile);

  const prompt = `
    Analyze this audio track from a video. 
    Identify the 3 most engaging, funny, or important sections suitable for short-form social media (TikTok/YouTube Shorts).
    Clips should be between 15 and 60 seconds.
    
    Return a JSON array where each object has:
    - "start": start time in seconds (number)
    - "end": end time in seconds (number)
    - "caption": a catchy, viral-style caption (string)
    - "hashtags": array of 3-5 hashtags (strings)
    - "explanation": brief reason why this part was chosen (string)

    Ensure the timestamps are accurate. Return ONLY valid JSON.
  `;

  try {
    const result = await model.generateContent([prompt, audioBase64]);
    const response = await result.response;
    const text = response.text();
    
    // Clean up markdown code blocks if present
    const jsonStr = text.replace(/```json/g, "").replace(/```/g, "").trim();
    return JSON.parse(jsonStr);
  } catch (error) {
    console.error("Gemini analysis failed:", error);
    throw error;
  }
}

async function fileToGenerativePart(file: File) {
  const base64EncodedDataPromise = new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
    reader.readAsDataURL(file);
  });
  
  return {
    inlineData: {
      data: await base64EncodedDataPromise as string,
      mimeType: file.type || "audio/mp3",
    },
  };
}
