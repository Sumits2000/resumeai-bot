const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  LevelFormat, HeadingLevel, BorderStyle, UnderlineType,
  ShadingType, TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');

// Read inputs from args
const type = process.argv[2];        // "resume" or "cover"
const contentFile = process.argv[3]; // path to text file with content
const outFile = process.argv[4];     // output path

const content = fs.readFileSync(contentFile, 'utf8');

// ── Color palette ────────────────────────────────────────────────────────────
const ACCENT   = "1D5C8E";   // professional dark blue
const ACCENT2  = "2E86C1";   // section rule color
const LIGHT    = "EBF5FB";   // header background
const DARK     = "1A252F";   // name text
const GRAY     = "5D6D7E";   // subtext

// ── Helpers ──────────────────────────────────────────────────────────────────
function sectionRule() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT2, space: 4 } },
    spacing: { before: 0, after: 120 },
    children: []
  });
}

function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 280, after: 60 },
    children: [new TextRun({
      text: text.toUpperCase(),
      bold: true,
      size: 22,
      color: ACCENT,
      font: "Calibri",
      characterSpacing: 40,
    })]
  });
}

function bulletLine(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: text.replace(/^[•\-\*]\s*/, '').trim(), size: 20, font: "Calibri", color: "1C1C1C" })]
  });
}

function bodyLine(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 40, after: 40 },
    children: [new TextRun({
      text,
      size: opts.size || 20,
      bold: opts.bold || false,
      italic: opts.italic || false,
      color: opts.color || "1C1C1C",
      font: "Calibri",
    })]
  });
}

function emptyLine() {
  return new Paragraph({ spacing: { before: 0, after: 60 }, children: [] });
}

// ── Resume parser ─────────────────────────────────────────────────────────────
function parseResume(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const children = [];

  // Header block
  const nameLine = lines[0] || "Your Name";
  const contactLine = lines[1] || "";

  // Name block with blue background
  children.push(new Paragraph({
    shading: { fill: LIGHT, type: ShadingType.CLEAR },
    spacing: { before: 0, after: 0 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: nameLine.replace(/\[|\]/g, ''),
      bold: true,
      size: 44,
      color: DARK,
      font: "Calibri",
    })]
  }));

  children.push(new Paragraph({
    shading: { fill: LIGHT, type: ShadingType.CLEAR },
    spacing: { before: 40, after: 200 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: contactLine.replace(/\[|\]/g, ''),
      size: 18,
      color: GRAY,
      font: "Calibri",
    })]
  }));

  // Parse rest of sections
  let i = 2;
  const SECTION_KEYWORDS = [
    'PROFESSIONAL SUMMARY', 'SUMMARY', 'WORK EXPERIENCE', 'EXPERIENCE',
    'SKILLS', 'EDUCATION', 'CERTIFICATIONS', 'PROJECTS', 'ACHIEVEMENTS'
  ];

  while (i < lines.length) {
    const line = lines[i];
    const isSection = SECTION_KEYWORDS.some(k => line.toUpperCase().startsWith(k));

    if (isSection) {
      children.push(sectionHeading(line));
      children.push(sectionRule());
    } else if (line.match(/^[•\-\*]/)) {
      children.push(bulletLine(line));
    } else if (line.includes('|') && !line.startsWith('|')) {
      // Job title | Company | Date line
      const parts = line.split('|').map(p => p.trim());
      const runParts = [];
      parts.forEach((p, idx) => {
        if (idx === 0) runParts.push(new TextRun({ text: p, bold: true, size: 20, font: "Calibri", color: "1C1C1C" }));
        else runParts.push(new TextRun({ text: " | " + p, size: 20, font: "Calibri", color: GRAY, italic: idx === parts.length - 1 }));
      });
      children.push(new Paragraph({ spacing: { before: 120, after: 40 }, children: runParts }));
    } else if (line.startsWith('Technical:') || line.startsWith('Soft Skills:')) {
      const [label, ...rest] = line.split(':');
      children.push(new Paragraph({
        spacing: { before: 60, after: 40 },
        children: [
          new TextRun({ text: label + ": ", bold: true, size: 20, font: "Calibri" }),
          new TextRun({ text: rest.join(':').trim(), size: 20, font: "Calibri", color: "1C1C1C" }),
        ]
      }));
    } else {
      children.push(bodyLine(line));
    }
    i++;
  }

  return children;
}

// ── Cover letter parser ───────────────────────────────────────────────────────
function parseCoverLetter(text) {
  const lines = text.split('\n').map(l => l.trim());
  const children = [];

  // Header bar
  children.push(new Paragraph({
    shading: { fill: LIGHT, type: ShadingType.CLEAR },
    spacing: { before: 0, after: 0 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "COVER LETTER", bold: true, size: 28, color: ACCENT, font: "Calibri", characterSpacing: 60 })]
  }));
  children.push(new Paragraph({
    shading: { fill: LIGHT, type: ShadingType.CLEAR },
    spacing: { before: 0, after: 240 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT2, space: 6 } },
    children: []
  }));

  for (const line of lines) {
    const t = line.trim();
    if (!t) { children.push(emptyLine()); continue; }

    if (t === 'Dear Hiring Manager,') {
      children.push(new Paragraph({
        spacing: { before: 120, after: 80 },
        children: [new TextRun({ text: t, bold: true, size: 22, font: "Calibri", color: DARK })]
      }));
    } else if (t === 'Sincerely,' || t === 'Regards,') {
      children.push(new Paragraph({
        spacing: { before: 200, after: 60 },
        children: [new TextRun({ text: t, size: 20, font: "Calibri" })]
      }));
    } else {
      children.push(new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { before: 60, after: 60, line: 320, lineRule: "auto" },
        children: [new TextRun({ text: t, size: 21, font: "Calibri", color: "1C1C1C" })]
      }));
    }
  }

  return children;
}

// ── Build document ────────────────────────────────────────────────────────────
const bodyChildren = type === 'resume' ? parseResume(content) : parseCoverLetter(content);

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "▸",
        alignment: AlignmentType.LEFT,
        style: {
          paragraph: { indent: { left: 480, hanging: 300 } },
          run: { font: "Calibri", color: ACCENT }
        }
      }]
    }]
  },
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 20, color: "1C1C1C" } }
    }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 900, right: 1080, bottom: 900, left: 1080 }
      }
    },
    children: bodyChildren
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outFile, buf);
  console.log('OK:' + outFile);
}).catch(e => {
  console.error('ERR:' + e.message);
  process.exit(1);
});
