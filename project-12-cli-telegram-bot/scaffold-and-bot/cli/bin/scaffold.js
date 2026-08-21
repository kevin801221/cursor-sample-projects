#!/usr/bin/env node
/**
 * Scaffold CLI
 * 支援: scaffold init <name> [--template react|fastapi] [--force]
 * 規範: 成功 exit(0)，失敗 exit(1)
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');

const G = '\x1b[1;32m';
const R = '\x1b[1;31m';
const Y = '\x1b[1;33m';
const B = '\x1b[1;36m';
const N = '\x1b[0m';

function printBanner() {
  console.log(`\n${B}======================================================${N}`);
  console.log(`${B}  ⚡ Scaffold CLI — 智慧專案腳手架生成器 (v1.0.0)${N}`);
  console.log(`${B}======================================================${N}\n`);
}

function showHelp() {
  printBanner();
  console.log(`用法:
  scaffold init <專案名稱> [選項]

選項:
  -t, --template <類型>  選擇專案模板 (react | fastapi) [預設: react]
  -f, --force            若目錄已存在則強制覆蓋
  -h, --help             顯示說明文件
  -v, --version          顯示版本號

範例:
  scaffold init my-frontend-app --template react
  scaffold init my-backend-api --template fastapi
`);
  process.exit(0);
}

function copyFolderSync(from, to) {
  fs.mkdirSync(to, { recursive: true });
  fs.readdirSync(from).forEach((element) => {
    const fromPath = path.join(from, element);
    const toPath = path.join(to, element);
    if (fs.lstatSync(fromPath).isDirectory()) {
      copyFolderSync(fromPath, toPath);
    } else {
      fs.copyFileSync(fromPath, toPath);
    }
  });
}

function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
    showHelp();
  }

  if (args.includes('-v') || args.includes('--version')) {
    console.log('scaffold-cli v1.0.0');
    process.exit(0);
  }

  const command = args[0];
  if (command !== 'init') {
    console.error(`${R}✗ 未知指令: ${command}${N}。請使用 ${Y}scaffold init <專案名稱>${N}`);
    process.exit(1);
  }

  const projectName = args[1];
  if (!projectName || projectName.startsWith('-')) {
    console.error(`${R}✗ 缺少專案名稱！${N} 範例: ${Y}scaffold init my-app${N}`);
    process.exit(1);
  }

  // Parse options
  let template = 'react';
  let force = false;

  for (let i = 2; i < args.length; i++) {
    if (args[i] === '-t' || args[i] === '--template') {
      template = args[i + 1] || 'react';
      i++;
    } else if (args[i] === '-f' || args[i] === '--force') {
      force = true;
    }
  }

  if (!['react', 'fastapi'].includes(template)) {
    console.error(`${R}✗ 不支援的模板類型: ${template}${N} (僅支援 react 或 fastapi)`);
    process.exit(1);
  }

  const targetDir = path.resolve(process.cwd(), projectName);

  if (fs.existsSync(targetDir) && !force) {
    console.error(`${R}✗ 目錄 '${projectName}' 已存在！${N}`);
    console.error(`  ${Y}↳ 提示：使用 --force 參數覆蓋，或指定其他目錄名稱${N}`);
    process.exit(1);
  }

  printBanner();
  console.log(`🚀 正在為您建立專案: ${B}${projectName}${N}`);
  console.log(`📦 套用藍圖模板: ${Y}${template}${N}`);

  const templateDir = path.join(ROOT_DIR, 'templates', template);
  copyFolderSync(templateDir, targetDir);

  console.log(`\n${G}✓ 專案建立完成！${N}`);
  console.log(`\n請執行以下指令開始開發：`);
  console.log(`  ${B}cd ${projectName}${N}`);
  if (template === 'react') {
    console.log(`  ${B}npm install && npm run dev${N}`);
  } else {
    console.log(`  ${B}uv sync && uv run uvicorn main:app --reload${N}`);
  }
  console.log();
  process.exit(0);
}

main();
