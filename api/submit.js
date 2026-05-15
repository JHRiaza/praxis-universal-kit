// PRAXIS Kit — Submit Endpoint (Vercel Serverless)
// Receives anonymized ZIP exports from PRAXIS participants
// Forwards to Gmail via Resend (or stores to GCS/Vercel Blob)

export const config = {
  maxDuration: 30,
  api: {
    bodyParser: false,
  },
};

// Simple file size limit check
const MAX_ZIP_SIZE = 10 * 1024 * 1024; // 10 MB

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  // Parse multipart form data manually (no external deps)
  const contentType = req.headers["content-type"] || "";
  if (!contentType.includes("multipart/form-data")) {
    return res.status(400).json({ error: "Expected multipart/form-data" });
  }

  try {
    // Collect raw body
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    const rawBody = Buffer.concat(chunks);

    if (rawBody.length > MAX_ZIP_SIZE) {
      return res.status(413).json({ error: "File too large (max 10 MB)" });
    }

    // Extract boundary and parse multipart
    const boundaryMatch = contentType.match(/boundary=(.+)/);
    if (!boundaryMatch) {
      return res.status(400).json({ error: "Invalid multipart boundary" });
    }
    const boundary = boundaryMatch[1].replace(/"/g, "");
    const parts = parseMultipart(rawBody, boundary);

    // Find the ZIP file part
    const zipPart = parts.find(
      (p) =>
        p.filename &&
        (p.filename.endsWith(".zip") || p.contentType === "application/zip")
    );

    if (!zipPart) {
      return res.status(400).json({ error: "No ZIP file found in upload" });
    }

    // Extract metadata
    const participantId = parts.find((p) => p.name === "participant_id")?.value || "UNKNOWN";
    const kitVersion = parts.find((p) => p.name === "kit_version")?.value || "unknown";

    // Validate participant ID format (PRAXIS-XXXXXXXX)
    if (!/^PRAXIS-[A-F0-9]{8}$/i.test(participantId)) {
      return res.status(400).json({ error: "Invalid participant ID format" });
    }

    // Store to Vercel Blob if configured, otherwise log
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const storageName = `${participantId}_${timestamp}.zip`;

    // Option 1: Forward via email (Resend)
    if (process.env.RESEND_API_KEY) {
      const emailResponse = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: "PRAXIS Kit <praxis@suehammervil.com>",
          to: ["hello@javierherreros.xyz"],
          subject: `PRAXIS submission [${participantId}] — ${storageName}`,
          text: [
            `New PRAXIS data submission received.`,
            ``,
            `Participant: ${participantId}`,
            `Kit version: ${kitVersion}`,
            `File: ${storageName}`,
            `Size: ${(zipPart.data.length / 1024).toFixed(1)} KB`,
            `Timestamp: ${timestamp}`,
            ``,
            `Attachment included in this email.`,
          ].join("\n"),
          attachments: [
            {
              filename: storageName,
              content: zipPart.data.toString("base64"),
            },
          ],
        }),
      });

      if (!emailResponse.ok) {
        const errText = await emailResponse.text();
        console.error("Resend error:", errText);
        // Fall through to blob storage
      } else {
        return res.status(200).json({
          status: "received",
          participant_id: participantId,
          storage_name: storageName,
          delivered_via: "email",
        });
      }
    }

    // Option 2: Store via Vercel Blob
    if (process.env.BLOB_READ_WRITE_TOKEN) {
      const { put } = await import("@vercel/blob");
      const blob = await put(`praxis-submissions/${storageName}`, zipPart.data, {
        access: "private",
        contentType: "application/zip",
      });

      return res.status(200).json({
        status: "received",
        participant_id: participantId,
        storage_name: storageName,
        delivered_via: "blob",
      });
    }

    // Fallback: just log (dev mode)
    console.log(
      `[PRAXIS] Submission received: ${participantId}, ${kitVersion}, ${(zipPart.data.length / 1024).toFixed(1)} KB`
    );

    return res.status(200).json({
      status: "received",
      participant_id: participantId,
      storage_name: storageName,
      delivered_via: "log",
      note: "No email or blob storage configured. Submission logged to console.",
    });
  } catch (err) {
    console.error("[PRAXIS] Submit error:", err);
    return res.status(500).json({ error: "Internal server error" });
  }
}

// Minimal multipart parser (no dependencies)
function parseMultipart(body, boundary) {
  const parts = [];
  const delimiter = Buffer.from(`--${boundary}`);
  const sections = splitBuffer(body, delimiter);

  for (const section of sections) {
    if (section.length === 0 || section.toString().startsWith("--")) continue;

    const headerEndIndex = section.indexOf("\r\n\r\n");
    if (headerEndIndex === -1) continue;

    const headerStr = section.slice(0, headerEndIndex).toString("utf-8");
    const data = section.slice(headerEndIndex + 4);
    // Remove trailing \r\n
    const trimmedData =
      data.length >= 2 && data[data.length - 2] === 0x0d && data[data.length - 1] === 0x0a
        ? data.slice(0, -2)
        : data;

    // Parse Content-Disposition
    const nameMatch = headerStr.match(/name="([^"]+)"/);
    const filenameMatch = headerStr.match(/filename="([^"]+)"/);
    const contentTypeMatch = headerStr.match(/Content-Type:\s*(.+)/i);

    const part = {
      name: nameMatch ? nameMatch[1] : null,
      filename: filenameMatch ? filenameMatch[1] : null,
      contentType: contentTypeMatch ? contentTypeMatch[1].trim() : null,
      data: trimmedData,
      value: null,
    };

    // If no filename, treat as text field
    if (!part.filename) {
      part.value = trimmedData.toString("utf-8");
    }

    parts.push(part);
  }

  return parts;
}

function splitBuffer(buf, delimiter) {
  const parts = [];
  let start = 0;

  while (start < buf.length) {
    const idx = buf.indexOf(delimiter, start);
    if (idx === -1) {
      parts.push(buf.slice(start));
      break;
    }
    parts.push(buf.slice(start, idx));
    start = idx + delimiter.length;
  }

  return parts;
}
