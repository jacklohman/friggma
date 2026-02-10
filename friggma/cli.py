import os
import click
from rich.console import Console
from rich.prompt import Confirm
from pathlib import Path
import subprocess
import shutil
import json

from .analyzer import DependencyAnalyzer

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Friggma - Set up Figma Make projects with Tailwind v4"""
    pass


@main.command()
@click.argument('src_folder', type=click.Path(exists=True))
# We remove the default here so we can trigger a manual prompt if needed
@click.option('-o', '--output', help='Output directory name')
@click.option('--keep-unused', is_flag=True, help='Keep unused components')
def init(src_folder, output, keep_unused):
    console.print("\n[bold blue]**Friggma Setup**[/bold blue]\n")
    
    # 1. Prompt for name if not provided via -o flag
    if not output:
        output = click.prompt("Enter a name for your project folder", default="friggma-project")
    
    src_path = Path(src_folder).resolve()
    output_path = Path(output).resolve()
    
    # 2. CREATE THE FOLDER (The missing piece)
    if not output_path.exists():
        console.print(f"[green]Creating folder: {output_path.name}...[/green]")
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        # If it exists, ask to overwrite
        if not Confirm.ask(f"[yellow]Folder '{output_path.name}' already exists. Overwrite contents?[/yellow]"):
            raise click.Abort()

    try:
        # Analyze dependencies
        console.print("[blue]Analyzing dependencies...[/blue]")
        analyzer = DependencyAnalyzer(src_path)
        deps = analyzer.analyze()
        
        console.print(f"Found {len(deps['npm_packages'])} npm packages")
        console.print(f"Found {len(deps['figma_ui_components'])} Figma UI components")
        
        # allocate config files
        console.print("[blue]Allocating config files...[/blue]")

        # Copy preset vite.config.ts
        template_dir = Path(__file__).parent / 'templates'
        temp_files = [
            'vite.config.ts',
            'tsconfig.json',
            'tsconfig.app.json',
            'tsconfig.node.json',
            'package.json',
            'index.html'
        ]

        for file in temp_files:
            src = template_dir / file
            dst = output_path / file
            shutil.copy(src, dst)
            console.print(f"✓ Added {file}", style="green")

        shutil.copytree(template_dir / 'public' , output_path / 'public')
        console.print("✓ Added public directory", style="green")
        
        # Copy user's src folder
        shutil.copytree(src_path, output_path / 'src')
        shutil.copy(template_dir / 'main.tsx', output_path / 'src' / 'main.tsx')
        console.print("✓ Copied src folder and added entry point main.tsx", style="green")

        # Copy tailwind fonts.css
        shutil.copy(template_dir / 'fonts.css', output_path / 'src' / 'styles' / 'fonts.css')
        console.print("✓ Added fonts.css", style="green")
        
        # Initialize npm 
        with console.status("[bold green]Running npm install..."):
            _install_npm(output_path)
        console.print("✓ Project initialized", style="green")

        # Install Tailwind v4
        with console.status("[bold green]Installing Tailwind CSS v4..."):
            _install_tailwind(output_path)
        console.print("✓ Tailwind CSS v4 installed", style="green")
        
        # Install detected dependencies
        if deps['npm_packages']:
            with console.status(f"[bold green]Installing {len(deps['npm_packages'])} dependencies..."):
                _install_dependencies(output_path, deps['npm_packages'])
            console.print(f"✓ Installed: {', '.join(deps['npm_packages'])}", style="green")
        
        # Remove unused components (optional)
        if not keep_unused:
            from .analyzer import ComponentAnalyzer
            analyzer = ComponentAnalyzer(output_path)
            with console.status("[bold green]Removing unused components..."):
                removed = analyzer.remove_unused()
            if removed > 0:
                console.print(f"✓ Removed {removed} unused components", style="green")
        
        # If success
        console.print(f"\n[bold pink]✓ Project ready at: {output_path}[/bold pink]\n")
        console.print("[blue]To start developing:[/blue]")
        console.print(f"  cd {output}")
        console.print(f"  npm run dev\n")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        raise click.Abort()


def _install_npm(output_path):
    # Install base dependencies
    subprocess.run(
        ['npm', 'install'],
        cwd=output_path,
        check=True,
        capture_output=True
    )


def _install_tailwind(output_path):
    """Install Tailwind CSS v4"""
    subprocess.run(
        ['npm', 'install', 'tailwindcss', '@tailwindcss/vite', "tw-animate-css"],
        cwd=output_path,
        check=True,
        capture_output=True
    )


def _install_dependencies(output_path, packages):
    # Just combine everything into one list
    # We include 'motion' (the bridge) and 'tw-animate-css' (the fix) by default
    all_deps = ["lucide-react", "framer-motion", "motion"]
    
    # Add any extra packages found by your scanner, avoiding duplicates
    if packages:
        all_deps = list(set(all_deps + packages))

    pkg_string = " ".join(all_deps)

    try:
        subprocess.run(
            f"npm install {pkg_string} --no-fund --no-audit",
            cwd=str(output_path),
            shell=True,
            check=True,
            env=os.environ.copy()
        )
        console.print("[green]✓ UI Engine Ready.[/green]")
    except subprocess.CalledProcessError:
        console.print("[red] Install failed. Run 'npm install' manually in the folder.[/red]")

if __name__ == '__main__':
    main()