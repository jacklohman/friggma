from importlib.metadata import files
import re
from pathlib import Path
from rich.console import Console

console = Console()


class DependencyAnalyzer:
    """Analyzes import statements to find required dependencies"""
    
    # Known Figma UI components (these come from Figma Make)
    FIGMA_UI_COMPONENTS = {
    "accordion", "alert-dialog", "alert", "aspect-ratio",
    "avatar", "badge", "breadcrumb", "button",
    "calendar", "card", "carousel", "chart",
    "checkbox", "collapsible", "command", "context-menu",
    "dialog", "drawer", "dropdown-menu", "form",
    "hover-card", "input-otp", "input", "label",
    "menubar", "navigation-menu", "pagination", "popover",
    "progress", "radio-group", "resizable", "scroll-area",
    "select", "separator", "sheet", "sidebar",
    "skeleton", "slider", "sonner", "switch",
    "table", "tabs", "textarea", "toggle-group",
    "toggle", "tooltip", "use-mobile", "utils",
    }
    
    def __init__(self, src_path):
        self._src_path = Path(src_path)
        self.src_path = self._src_path / 'app' / 'components' 
        
    def analyze(self):
        """
        Analyze all files to find dependencies
        
        Returns:
            dict with:
            - npm_packages: list of external packages to install
            - figma_ui_components: list of Figma UI components used
        """
        npm_packages = set()
        figma_components = set()
        
        # Find all JS/TS files
        files = list(self.src_path.glob('*.js')) + \
                list(self.src_path.glob('*.jsx')) + \
                list(self.src_path.glob('*.ts')) + \
                list(self.src_path.glob('*.tsx'))
        
        for file in files:
            imports = self._extract_imports(file)
            
            for imp in imports:
                if self._is_npm_package(imp):
                    # Skip react and react-dom (already in Vite template)
                    if imp not in ['react', 'react-dom', 'react/jsx-runtime']:
                        npm_packages.add(imp)
                elif self._is_figma_component(imp):
                    figma_components.add(imp)
        
        return {
            'npm_packages': sorted(list(npm_packages)),
            'figma_ui_components': sorted(list(figma_components))
        }
    
    def _extract_imports(self, file_path):
        """Extract all import statements from a file"""
        imports = []
        
        try:
            content = file_path.read_text()
            
            # Match: import X from 'package'
            # Match: import { X } from 'package'
            # Match: import * as X from 'package'
            patterns = [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'import\s+[\'"]([^\'"]+)[\'"]',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    imports.append(match.group(1))
                    
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        return imports
    
    def _is_npm_package(self, import_path):
        """Check if import is an npm package (not relative/absolute)"""
        # npm packages don't start with . or /
        return not import_path.startswith('.') and not import_path.startswith('/')
    
    def _is_figma_component(self, import_path):
        """Check if import path includes a known Figma UI component"""
        # Check if any Figma component name is in the path
        return any(comp in import_path for comp in self.FIGMA_UI_COMPONENTS)


class ComponentAnalyzer:
    """Analyzes React components to find and remove unused ones"""
    
    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.src_dir = self.project_dir / 'src' / 'app'
        self.components_dir = self.src_dir / 'components' / 'ui'
        
    def remove_unused(self):
        """Find and delete unused components"""
        if not self.components_dir.exists():
            return 0
        
        # Find all component files
        component_files = list(self.components_dir.glob('*.jsx')) + \
                         list(self.components_dir.glob('*.tsx'))
        
        if not component_files:
            return 0
        
        # Find which are used
        used_components = self._find_used_components()
        
        # Delete unused
        removed = 0
        for comp_file in component_files:
            comp_name = comp_file.stem
            if comp_name not in used_components:
                comp_file.unlink()
                removed += 1
        
        return removed
    
    def _find_used_components(self):
        """Find all components that are imported"""
        used = set()
        
        # Scan entry files (everything in src root)
        entry_files = list(self.src_dir.glob('*.jsx')) + \
                     list(self.src_dir.glob('*.tsx')) + \
                     list(self.src_dir.glob('*.js')) + \
                     list(self.src_dir.glob('*.ts'))
        
        for file in entry_files:
            self._scan_imports(file, used)
        
        # Recursively check components importing other components
        checked = set()
        to_check = list(used)
        
        while to_check:
            comp = to_check.pop(0)
            if comp in checked:
                continue
            checked.add(comp)
            
            comp_file = self._find_component_file(comp)
            if comp_file:
                new_imports = set()
                self._scan_imports(comp_file, new_imports)
                for new_comp in new_imports:
                    if new_comp not in used:
                        used.add(new_comp)
                        to_check.append(new_comp)
        
        return used
    
    def _scan_imports(self, file_path, used_set):
        """Scan file for component imports"""
        try:
            content = file_path.read_text()
            
            # Match different import patterns for local components
            patterns = [
                # Handles: import Button from "./components/ui/Button"
                r'import\s+(\w+)\s+from\s+[\'"]\.\/components\/ui\/(\w+)[\'"]',
                # Handles: import { Button } from "./components/ui"
                r'import\s+\{([^}]+)\}\s+from\s+[\'"]\.\/components\/ui[\'"]',
                # Handles: import { Button } from "./components/ui/Button"
                r'import\s+\{([^}]+)\}\s+from\s+[\'"]\.\/components\/ui\/\w+[\'"]'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    if len(match.groups()) == 2:
                        used_set.add(match.group(2))
                    else:
                        imports = match.group(1).split(',')
                        for imp in imports:
                            comp_name = imp.strip().split(' as ')[0].strip()
                            used_set.add(comp_name)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not scan {file_path}: {e}[/yellow]")
    
    def _find_component_file(self, comp_name):
        """Find component file by name"""
        possible_files = list(self.components_dir.rglob(f'{comp_name}.jsx')) + \
                        list(self.components_dir.rglob(f'{comp_name}.tsx'))
        return possible_files[0] if possible_files else None