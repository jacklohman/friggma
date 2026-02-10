# Friggma

Quickly set up Figma Make projects with Tailwind CSS v4 and proper dependencies.

## Why?

Simplifies local setup of Figma make projects;
Figma make automatically installs npm and ui components that often go unused.
Friggma removes this Figma bloat, and sets the project up on your local machine in one command.

## Installation
```bash
pip install friggma
```

## Usage

### Step 1: Download from Figma Make

In Figma Make:
1. Click on the **"Code"** tab
2. Right-click on the **"src"** folder
3. Click **"Download"**

You'll get a `src` folder (extract if `src.zip`).

### Step 2: Run Friggma
```bash
frig init path/to/downloaded/src
```

Friggma will:
- Create a Vite + React + TypeScript project
- Install Tailwind CSS v4
- Analyze your imports and install required packages
- Remove unused components
- Set up the correct vite.config.ts

### Step 3: Start Developing
```bash
cd friggma-project
npm run dev
```

## Options
```bash
# Specify output directory
frig init path/to/src --output my-cool-project

# Keep unused components (don't remove them)
frig init path/to/src --keep-unused
```

## What It Does

1. **Analyzes dependencies**: Scans all import statements to find npm packages
2. **Creates Vite project**: Scaffolds a fresh Vite + React + TypeScript project
3. **Replaces src folder**: Removes the default Vite src and uses yours
4. **Installs Tailwind v4**: Adds `tailwindcss@next` and `@tailwindcss/vite@next`
5. **Installs packages**: Auto-installs detected npm packages from your imports
6. **Removes unused components**: Analyzes which components are actually imported
7. **Configures Vite**: Uses a preset vite.config.ts with Tailwind plugin

## Example
```bash
# Download src folder from Figma Make
# Then:

$ frig init ~/Downloads/src

Friggma Setup

Analyzing dependencies...
Found 3 npm packages
Found 5 Figma UI components
✓ Vite project created
Replacing with your files...
✓ Copied your src folder
✓ Added Vite config
✓ Tailwind CSS v4 installed
✓ Installed: lucide-react, clsx, tailwind-merge
✓ Removed 12 unused components

✓ Project ready at: /Users/you/friggma-project

To start developing:
  cd friggma-project
  npm run dev
```

## Common Issues

### "Module not found"

If you get import errors, you might need to manually install some packages:
```bash
npm install package-name
```

This usually happens with TypeScript type definitions.

### Components not working

Make sure your src folder includes:
- All component files
- The CSS file with Tailwind imports
- Any utility files (lib/, utils/, etc.)

## Development
```bash
git clone https://github.com/yourusername/friggma.git
cd friggma
pip install -e .

# Test it
frig init path/to/src --output test-project
```

## License

MIT