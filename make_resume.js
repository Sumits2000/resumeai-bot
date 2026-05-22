'use strict';
// ResumeAI — DOCX generator
// Called by Python: node make_resume.js <type> <input.txt> <output.docx>

const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

// Find docx module — local node_modules first, then global, then auto-install
function loadDocx() {
  const localPath = path.join(__dirname, 'node_modules', 'docx');
  if (fs.existsSync(localPath)) return require(localPath);
  try { return require('docx'); } catch(e) {}
  console.error('docx not found, installing...');
  execSync('npm install docx', { cwd: __dirname, stdio: 'inherit' });
  return require(path.join(__dirname, 'node_modules', 'docx'));
}

const {
  Document, Packer, Paragraph, TextRun,
  AlignmentType, BorderStyle, ShadingType,
  LevelFormat, UnderlineType,
} = loadDocx();

const [,, type, inputFile, outputFile] = process.argv;

if (!type || !inputFile || !outputFile) {
  console.error('Usage: node make_resume.js <resume|cover> <input.txt> <output.docx>');
  process.exit(1);
}

const raw = fs.readFileSync(inputFile, 'utf8');

// ── Design tokens ────────────────────────────────────────────────────────────
const C = {
  accent:   '1D5C8E',
  accent2:  '2980B9',
  dark:     '1A252F',
  gray:     '5D6D7E',
  lightbg:  'EBF5FB',
  black:    '1C1C1C',
};

// ── Helpers ──────────────────────────────────────────────────────────────────
const empty = (sp = 80) => new Paragraph({ spacing: { before: 0, after: sp }, children: [] });

const rule = () => new Paragraph({
  border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: C.accent2, space: 3 } },
  spacing: { before: 0, after: 100 },
  children: [],
});

const sectionHead = (text) => new Paragraph({
  spacing: { before: 240, after: 60 },
  children: [new TextRun({
    text: text.toUpperCase(),
    bold: true, size: 22,
    color: C.accent, font: 'Calibri',
    characterSpacing: 50,
  })],
});

const bullet = (text) => new Paragraph({
  numbering: { reference: 'bullets', level: 0 },
  spacing: { before: 30, after: 30 },
  children: [new TextRun({
    text: text.replace(/^[•▸\-\*]\s*/, '').trim(),
    size: 20, font: 'Calibri', color: C.black,
  })],
});

const bodyPara = (text, opts = {}) => new Paragraph({
  alignment: opts.align || AlignmentType.LEFT,
  spacing: { before: opts.before || 40, after: opts.after || 40, line: opts.line || 276, lineRule: 'auto' },
  children: [new TextRun({
    text, size: opts.size || 20, bold: opts.bold || false,
    italic: opts.italic || false, color: opts.color || C.black,
    font: 'Calibri',
  })],
});

// ── Resume builder ────────────────────────────────────────────────────────────
function buildResume(text) {
  const lines = text.split('\n').map(l => l.trim());
  const out = [];

  const SECTIONS = [
    'PROFESSIONAL SUMMARY','SUMMARY','PROFILE',
    'WORK EXPERIENCE','EXPERIENCE','EMPLOYMENT',
    'SKILLS','TECHNICAL SKILLS','KEY SKILLS',
    'EDUCATION','ACADEMIC',
    'CERTIFICATIONS','CERTIFICATES',
    'PROJECTS','ACHIEVEMENTS','AWARDS',
  ];

  // Header — name + contact
  const nameLine = lines.find(l => l.length > 0) || 'Your Name';
  const contactLine = lines.find((l, i) => i > 0 && i < 5 && l.includes('|')) || '';

  out.push(new Paragraph({
    shading: { fill: C.lightbg, type: ShadingType.CLEAR },
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 60 },
    children: [new TextRun({
      text: nameLine.replace(/\[|\]/g, '').replace(/^\*+|\*+$/g, ''),
      bold: true, size: 48, color: C.dark, font: 'Calibri',
    })],
  }));

  if (contactLine) {
    out.push(new Paragraph({
      shading: { fill: C.lightbg, type: ShadingType.CLEAR },
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 180 },
      children: [new TextRun({
        text: contactLine.replace(/\[|\]/g, ''),
        size: 18, color: C.gray, font: 'Calibri',
      })],
    }));
  } else {
    out.push(empty(180));
  }

  // Body lines
  let startIdx = contactLine ? 2 : 1;
  for (let i = startIdx; i < lines.length; i++) {
    const line = lines[i];
    if (!line) { out.push(empty(60)); continue; }

    const upper = line.toUpperCase().replace(/\*+/g, '').trim();
    const isSection = SECTIONS.some(s => upper === s || upper.startsWith(s));

    if (isSection) {
      out.push(sectionHead(line.replace(/\*+/g, '').trim()));
      out.push(rule());
    } else if (/^[•▸\-\*]/.test(line)) {
      out.push(bullet(line));
    } else if (line.includes('|') && !line.startsWith('|') && line.split('|').length >= 2) {
      // Job title | Company | Date
      const parts = line.split('|').map(p => p.trim().replace(/\*+/g, ''));
      const runs = [];
      parts.forEach((p, idx) => {
        if (idx === 0) {
          runs.push(new TextRun({ text: p, bold: true, size: 20, font: 'Calibri', color: C.black }));
        } else {
          runs.push(new TextRun({ text: '  |  ' + p, size: 19, font: 'Calibri', color: C.gray, italic: idx === parts.length - 1 }));
        }
      });
      out.push(new Paragraph({ spacing: { before: 140, after: 40 }, children: runs }));
    } else if (/^(Technical|Soft Skills|Tools|Languages|Frameworks):/i.test(line)) {
      const colon = line.indexOf(':');
      const label = line.slice(0, colon + 1);
      const value = line.slice(colon + 1).trim();
      out.push(new Paragraph({
        spacing: { before: 50, after: 40 },
        children: [
          new TextRun({ text: label + ' ', bold: true, size: 20, font: 'Calibri', color: C.black }),
          new TextRun({ text: value, size: 20, font: 'Calibri', color: C.black }),
        ],
      }));
    } else {
      out.push(bodyPara(line.replace(/\*+/g, '')));
    }
  }

  return out;
}

// ── Cover letter builder ──────────────────────────────────────────────────────
function buildCover(text) {
  const lines = text.split('\n').map(l => l.trim());
  const out = [];

  // Title bar
  out.push(new Paragraph({
    shading: { fill: C.lightbg, type: ShadingType.CLEAR },
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0 },
    children: [new TextRun({
      text: 'COVER LETTER',
      bold: true, size: 30, color: C.accent,
      font: 'Calibri', characterSpacing: 80,
    })],
  }));
  out.push(new Paragraph({
    shading: { fill: C.lightbg, type: ShadingType.CLEAR },
    border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: C.accent2, space: 6 } },
    spacing: { before: 0, after: 220 },
    children: [],
  }));

  for (const line of lines) {
    if (!line) { out.push(empty(100)); continue; }

    if (line.toLowerCase().startsWith('dear')) {
      out.push(bodyPara(line, { bold: true, size: 21, before: 100, after: 80 }));
    } else if (/^(sincerely|regards|yours|warm regards)/i.test(line)) {
      out.push(bodyPara(line, { before: 220, after: 60 }));
    } else {
      out.push(bodyPara(line, { align: AlignmentType.JUSTIFIED, line: 320, before: 60, after: 60 }));
    }
  }

  return out;
}

// ── Assemble document ─────────────────────────────────────────────────────────
const bodyChildren = type === 'resume' ? buildResume(raw) : buildCover(raw);

const doc = new Document({
  numbering: {
    config: [{
      reference: 'bullets',
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: '▸',
        alignment: AlignmentType.LEFT,
        style: {
          paragraph: { indent: { left: 480, hanging: 320 } },
          run: { font: 'Calibri', color: C.accent },
        },
      }],
    }],
  },
  styles: {
    default: {
      document: { run: { font: 'Calibri', size: 20, color: C.black } },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 900, right: 1080, bottom: 900, left: 1080 },
      },
    },
    children: bodyChildren,
  }],
});

Packer.toBuffer(doc)
  .then(buf => {
    fs.writeFileSync(outputFile, buf);
    console.log('OK:' + outputFile + ':' + buf.length);
  })
  .catch(err => {
    console.error('DOCX_ERR:' + err.message);
    process.exit(1);
  });
