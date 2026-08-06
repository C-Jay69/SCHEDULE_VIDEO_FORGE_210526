import ZAI from "z-ai-web-dev-sdk";
import { db } from "./db";
import { execSync, exec } from "child_process";
import fs from "fs";
import path from "path";
import { v4 as uuidv4 } from "uuid";

interface Scene {
  narration: string;
  imagePrompt: string;
}

interface ScriptResult {
  title: string;
  scenes: Scene[];
}

function getWorkDir(videoId: string) {
  const dir = path.join(process.cwd(), ".tmp", videoId);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function splitTextIntoChunks(text: string, maxLength = 950) {
  const chunks: string[] = [];
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  let current = "";
  for (const sentence of sentences) {
    if ((current + sentence).length <= maxLength) {
      current += sentence;
    } else {
      if (current) chunks.push(current.trim());
      current = sentence;
    }
  }
  if (current) chunks.push(current.trim());
  return chunks;
}

async function generateScript(topic: string, tone: string, style: string, duration: number): Promise<ScriptResult> {
  const zai = await ZAI.create();

  const sceneCount = duration <= 30 ? 2 : duration <= 60 ? 3 : duration <= 180 ? 4 : 5;

  const completion = await zai.chat.completions.create({
    messages: [
      {
        role: "assistant",
        content: `You are a professional short-form video scriptwriter. You write engaging, ${tone} scripts for ${style}-style videos.

CRITICAL: You MUST respond with valid JSON only. No markdown, no code blocks, no extra text.

The JSON must have this exact structure:
{
  "title": "A catchy video title under 60 characters",
  "scenes": [
    {
      "narration": "The spoken narration text for this scene (1-3 sentences)",
      "imagePrompt": "A detailed description for generating an AI image for this scene, describing the visual content. Include style, mood, lighting, colors."
    }
  ]
}

Rules:
- Generate exactly ${sceneCount} scenes
- Each narration should be 30-80 words
- Image prompts should be descriptive and cinematic
- The total narration should be roughly ${duration} seconds when spoken
- Make it engaging and suitable for short-form video (YouTube Shorts, TikTok, Reels)`,
      },
      {
        role: "user",
        content: `Write a video script about: ${topic}`,
      },
    ],
    thinking: { type: "disabled" },
  });

  let raw = completion.choices[0]?.message?.content || "";
  // Strip markdown code fences if present
  raw = raw.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();

  try {
    const parsed = JSON.parse(raw);
    if (!parsed.scenes || !Array.isArray(parsed.scenes) || parsed.scenes.length === 0) {
      throw new Error("No scenes in response");
    }
    return parsed as ScriptResult;
  } catch {
    // Fallback script
    return {
      title: topic.length > 60 ? topic.slice(0, 57) + "..." : topic,
      scenes: [
        {
          narration: `Here's an interesting look at ${topic}. This topic has been gaining a lot of attention lately, and for good reason. Let's break down what makes it so compelling and why you should care about it.`,
          imagePrompt: `Cinematic wide shot of ${topic}, dramatic lighting, professional photography style, 4K quality, vibrant colors, modern aesthetic`,
        },
        {
          narration: `The key insight here is that ${topic} represents a fundamental shift in how we think about this space. The implications are far-reaching and affect everyone from creators to consumers.`,
          imagePrompt: `Close-up detail shot related to ${topic}, shallow depth of field, warm golden hour lighting, professional cinematography, cinematic mood`,
        },
        {
          narration: `So what do you think about ${topic}? Drop your thoughts in the comments below, and if you found this valuable, make sure to follow for more content like this. See you in the next one!`,
          imagePrompt: `Inspiring final scene, person looking at horizon, sunset colors, motivational atmosphere, cinematic wide angle, professional quality`,
        },
      ],
    };
  }
}

async function generateAudioForScene(narration: string, outputPath: string, zai: any): Promise<number> {
  const chunks = splitTextIntoChunks(narration);
  const chunkFiles: string[] = [];

  for (let i = 0; i < chunks.length; i++) {
    const chunkPath = outputPath.replace(/\.wav$/, `_chunk${i}.wav`);
    const response = await zai.audio.tts.create({
      input: chunks[i],
      voice: "kazi",
      speed: 1.0,
      response_format: "wav",
      stream: false,
    });
    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(new Uint8Array(arrayBuffer));
    fs.writeFileSync(chunkPath, buffer);
    chunkFiles.push(chunkPath);
  }

  if (chunkFiles.length === 1) {
    fs.renameSync(chunkFiles[0], outputPath);
  } else {
    // Concatenate WAV files using FFmpeg
    const listFile = outputPath.replace(/\.wav$/, "_list.txt");
    fs.writeFileSync(listFile, chunkFiles.map((f) => `file '${f}'`).join("\n"));
    execSync(`ffmpeg -y -f concat -safe 0 -i "${listFile}" -c copy "${outputPath}" 2>/dev/null`);
    chunkFiles.forEach((f) => { if (fs.existsSync(f)) fs.unlinkSync(f); });
    if (fs.existsSync(listFile)) fs.unlinkSync(listFile);
  }

  // Get duration
  const probe = execSync(`ffprobe -v quiet -print_format json -show_format "${outputPath}"`);
  const info = JSON.parse(probe.toString());
  return parseFloat(info.format.duration) || 10;
}

async function generateSceneImage(prompt: string, outputPath: string, zai: any, format: string): Promise<void> {
  const size = format === "short-form" ? "768x1344" : format === "landscape" ? "1344x768" : "1024x1024";

  try {
    const response = await zai.images.generations.create({
      prompt: `${prompt}, high quality, cinematic, professional`,
      size,
    });
    const base64 = response.data[0].base64;
    const buffer = Buffer.from(base64, "base64");
    fs.writeFileSync(outputPath, buffer);
  } catch (err) {
    console.error("Image generation failed, creating gradient fallback:", err);
    // Create a gradient fallback image using FFmpeg
    const colors = [
      "0x1a0533", "0x2d1b69", "0x11998e", "0x38ef7d",
      "0x0f0c29", "0x302b63", "0x24243e",
    ];
    const c1 = colors[Math.floor(Math.random() * colors.length)];
    const c2 = colors[Math.floor(Math.random() * colors.length)];
    const w = format === "short-form" ? 1080 : format === "landscape" ? 1920 : 1080;
    const h = format === "short-form" ? 1920 : format === "landscape" ? 1080 : 1080;
    execSync(
      `ffmpeg -y -f lavfi -i "gradients=c0=${c1}:c1=${c2}:w=${w}:h=${h}:duration=1" -frames:v 1 "${outputPath}" 2>/dev/null`
    );
  }
}

function assembleVideo(
  workDir: string,
  sceneImages: string[],
  audioPath: string,
  sceneDurations: number[],
  outputPath: string,
  title: string,
  format: string
): void {
  const w = format === "short-form" ? 1080 : format === "landscape" ? 1920 : 1080;
  const h = format === "short-form" ? 1920 : format === "landscape" ? 1080 : 1080;

  // Scale each image to exact dimensions
  const scaledImages = sceneImages.map((img, i) => {
    const scaled = path.join(workDir, `scene_${i}_scaled.png`);
    execSync(`ffmpeg -y -i "${img}" -vf "scale=${w}:${h}:force_original_aspect_ratio=decrease,pad=${w}:${h}:(ow-iw)/2:(oh-ih)/2:black" "${scaled}" 2>/dev/null`);
    return scaled;
  });

  // Create concat file for images with durations
  const concatFile = path.join(workDir, "concat.txt");
  let concatContent = "";
  for (let i = 0; i < scaledImages.length; i++) {
    const dur = sceneDurations[i] || 5;
    concatContent += `file '${scaledImages[i]}'\n`;
    concatContent += `duration ${dur}\n`;
  }
  // Add last image again (ffmpeg concat demuxer requirement)
  concatContent += `file '${scaledImages[scaledImages.length - 1]}'\n`;
  fs.writeFileSync(concatFile, concatContent);

  // Get audio duration
  const probe = execSync(`ffprobe -v quiet -print_format json -show_format "${audioPath}"`);
  const audioInfo = JSON.parse(probe.toString());
  const totalAudioDur = parseFloat(audioInfo.format.duration) || 30;

  // Create subtitle-like text overlay with scene transitions
  // Use xfade for transitions between scenes
  const transitionDur = 0.5;

  // Build FFmpeg command with zoompan (Ken Burns effect) per scene
  let complexFilter = "";
  let inputs = "";

  for (let i = 0; i < scaledImages.length; i++) {
    inputs += ` -loop 1 -framerate 30 -t ${sceneDurations[i] + transitionDur} -i "${scaledImages[i]}"`;
  }
  inputs += ` -i "${audioPath}"`;

  // Apply zoompan for cinematic feel
  const zoomPanFilters = scaledImages.map((_, i) => {
    const zoomStart = 1.0;
    const zoomEnd = 1.15;
    const xStart = 0;
    const xEnd = 20;
    const yStart = 0;
    const yEnd = 10;
    return `[${i}:v]scale=${w}:${h},zoompan=z='min(${zoomStart}+(${zoomEnd}-${zoomStart})*on/${sceneDurations[i] < 10 ? 300 : 600},${zoomEnd})':d=${Math.ceil((sceneDurations[i] + transitionDur) * 30)}:s=${w}x${h}:x='iw/2-(iw/zoom/2)+${i % 2 === 0 ? "" : "-"}${xEnd}*on/${sceneDurations[i] < 10 ? 300 : 600}':y='ih/2-(ih/zoom/2)+${i % 2 === 0 ? "" : "-"}${yEnd}*on/${sceneDurations[i] < 10 ? 300 : 600}',fps=30[v${i}];`;
  });

  // Chain xfade transitions
  let xfadeChain = "";
  if (scaledImages.length === 1) {
    xfadeChain = `[v0]null[outv]`;
  } else {
    let prevLabel = `v0`;
    for (let i = 1; i < scaledImages.length; i++) {
      const offset = sceneDurations.slice(0, i).reduce((a, b) => a + b, 0) + transitionDur * (i - 1);
      const outLabel = i === scaledImages.length - 1 ? "outv" : `xf${i}`;
      xfadeChain += `[${prevLabel}][v${i}]xfade=transition=fade:duration=${transitionDur}:offset=${offset}[${outLabel}];`;
      prevLabel = outLabel;
    }
  }

  complexFilter = zoomPanFilters.join("") + xfadeChain;

  const audioIdx = scaledImages.length;
  const cmd = `ffmpeg -y${inputs} -filter_complex "${complexFilter}" -map "[outv]" -map "${audioIdx}:a" -t ${totalAudioDur} -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -pix_fmt yuv420p -movflags +faststart -shortest "${outputPath}" 2>/dev/null`;

  try {
    execSync(cmd, { timeout: 120000 });
  } catch (err) {
    console.error("Complex FFmpeg failed, using simpler approach:", err);
    // Fallback: simple concat without transitions
    const simpleCmd = `ffmpeg -y -f concat -safe 0 -i "${concatFile}" -i "${audioPath}" -vf "scale=${w}:${h}:force_original_aspect_ratio=decrease,pad=${w}:${h}:(ow-iw)/2:(oh-ih)/2,fps=30" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -pix_fmt yuv420p -movflags +faststart -shortest "${outputPath}" 2>/dev/null`;
    execSync(simpleCmd, { timeout: 120000 });
  }

  // Add title text overlay as a second pass (burn it in)
  const finalOutput = outputPath.replace(/\.mp4$/, "_final.mp4");
  const escapedTitle = title.replace(/'/g, "'\\''").replace(/:/g, "\\:");
  execSync(
    `ffmpeg -y -i "${outputPath}" -vf "drawtext=text='${escapedTitle}':fontcolor=white:fontsize=36:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:x=(w-text_w)/2:y=40:box=1:boxcolor=black@0.5:boxborderw=8,drawtext=text='VideoForge':fontcolor=white@0.3:fontsize=20:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:x=(w-text_w)/2:y=h-40" -c:v libx264 -preset fast -crf 23 -c:a copy -movflags +faststart "${finalOutput}" 2>/dev/null`
  );

  if (fs.existsSync(finalOutput)) {
    fs.renameSync(finalOutput, outputPath);
  }
}

export async function generateVideo(
  videoId: string,
  userId: string,
  topic: string,
  tone: string,
  style: string,
  duration: number,
  format: string
): Promise<void> {
  const workDir = getWorkDir(videoId);

  try {
    // Update status
    await db.video.update({ where: { id: videoId }, data: { status: "processing", progress: 5 } });

    // Phase 1: Generate script
    await db.video.update({ where: { id: videoId }, data: { progress: 10 } });
    console.log(`[Pipeline ${videoId}] Generating script...`);
    const script = await generateScript(topic, tone, style, duration);
    await db.video.update({
      where: { id: videoId },
      data: { title: script.title, scriptText: JSON.stringify(script), progress: 25 },
    });
    console.log(`[Pipeline ${videoId}] Script generated: ${script.scenes.length} scenes`);

    const zai = await ZAI.create();

    // Phase 2: Generate audio for each scene
    const audioPaths: string[] = [];
    const sceneDurations: number[] = [];

    for (let i = 0; i < script.scenes.length; i++) {
      const audioPath = path.join(workDir, `scene_${i}.wav`);
      console.log(`[Pipeline ${videoId}] Generating audio for scene ${i + 1}/${script.scenes.length}...`);
      const dur = await generateAudioForScene(script.scenes[i].narration, audioPath, zai);
      audioPaths.push(audioPath);
      sceneDurations.push(dur);
      await db.video.update({
        where: { id: videoId },
        data: { progress: 25 + Math.floor(((i + 1) / script.scenes.length) * 30) },
      });
    }

    // Concatenate all audio into one file
    const fullAudioPath = path.join(workDir, "full_audio.wav");
    if (audioPaths.length === 1) {
      fs.copyFileSync(audioPaths[0], fullAudioPath);
    } else {
      const audioList = path.join(workDir, "audio_list.txt");
      fs.writeFileSync(audioList, audioPaths.map((f) => `file '${f}'`).join("\n"));
      execSync(`ffmpeg -y -f concat -safe 0 -i "${audioList}" -c copy "${fullAudioPath}" 2>/dev/null`);
    }

    // Phase 3: Generate scene images
    const imagePaths: string[] = [];
    for (let i = 0; i < script.scenes.length; i++) {
      const imgPath = path.join(workDir, `scene_${i}.png`);
      console.log(`[Pipeline ${videoId}] Generating image for scene ${i + 1}/${script.scenes.length}...`);
      await generateSceneImage(script.scenes[i].imagePrompt, imgPath, zai, format);
      imagePaths.push(imgPath);
      await db.video.update({
        where: { id: videoId },
        data: { progress: 55 + Math.floor(((i + 1) / script.scenes.length) * 25) },
      });
    }

    // Phase 4: Assemble video
    console.log(`[Pipeline ${videoId}] Assembling video...`);
    await db.video.update({ where: { id: videoId }, data: { progress: 85 } });

    const outputFileName = `${videoId}_${Date.now()}.mp4`;
    const outputPath = path.join(workDir, outputFileName);

    assembleVideo(workDir, imagePaths, fullAudioPath, sceneDurations, outputPath, script.title, format);

    // Phase 5: Move to uploads
    const uploadDir = path.join(process.cwd(), "uploads", "videos");
    if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

    const finalPath = path.join(uploadDir, outputFileName);
    fs.renameSync(outputPath, finalPath);

    // Get final video duration
    const probe = execSync(`ffprobe -v quiet -print_format json -show_format "${finalPath}"`);
    const info = JSON.parse(probe.toString());
    const finalDuration = Math.ceil(parseFloat(info.format.duration)) || duration;

    // Update video record
    await db.video.update({
      where: { id: videoId },
      data: {
        status: "completed",
        storageKey: outputFileName,
        duration: finalDuration,
        progress: 100,
      },
    });

    console.log(`[Pipeline ${videoId}] Video generated successfully: ${finalPath}`);

    // Cleanup temp files (keep the final video)
    try {
      const tmpDir = path.join(process.cwd(), ".tmp");
      if (fs.existsSync(tmpDir)) {
        fs.rmSync(tmpDir, { recursive: true, force: true });
      }
    } catch {}
  } catch (err: any) {
    console.error(`[Pipeline ${videoId}] Generation failed:`, err);
    await db.video.update({
      where: { id: videoId },
      data: { status: "failed", error: err.message || "Unknown error", progress: 0 },
    });
    // Cleanup
    try {
      const tmpDir = path.join(process.cwd(), ".tmp");
      if (fs.existsSync(tmpDir)) {
        fs.rmSync(tmpDir, { recursive: true, force: true });
      }
    } catch {}
  }
}
