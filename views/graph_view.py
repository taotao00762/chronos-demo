# ===========================================================================
# Chronos AI Learning Companion
# File: views/graph_view.py
# Purpose: Knowledge Graph visualization using PyVis
# ===========================================================================

"""
Knowledge Graph View

Interactive visualization of learning concepts and their relationships.
Uses PyVis to generate an interactive graph opened in browser.
"""

import flet as ft
import webbrowser
from pathlib import Path
from styles.tokens import Colors, Sizes
from styles.glass import GlassContainer


# Graph HTML output path
GRAPH_HTML_PATH = Path("data/knowledge_graph.html")


def create_graph_view() -> ft.Container:
    """Create the Knowledge Graph view with PyVis integration."""
    
    # State
    state = {"page": None, "graph_generated": False, "node_count": 0, "edge_count": 0}
    
    # Status text
    status_text = ft.Text("", size=13, color=Colors.TEXT_SECONDARY)
    
    # Loading indicator
    loading = ft.Column(
        controls=[
            ft.ProgressRing(width=32, height=32, stroke_width=3),
            ft.Container(height=12),
            ft.Text("Generating knowledge graph...", size=14, color=Colors.TEXT_SECONDARY),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )
    
    # Success state
    success_state = ft.Column(
        controls=[
            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=64, color="#22C55E"),
            ft.Container(height=16),
            ft.Text("Graph Generated!", size=20, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Container(height=8),
            status_text,
            ft.Container(height=24),
            ft.FilledButton(
                text="Open in Browser",
                icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                style=ft.ButtonStyle(bgcolor=Colors.TEXT_PRIMARY, color=Colors.BG_PRIMARY),
                on_click=lambda e: open_graph(),
            ),
            ft.Container(height=12),
            ft.OutlinedButton(
                text="Regenerate",
                icon=ft.Icons.REFRESH_ROUNDED,
                style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY),
                on_click=lambda e: generate_graph(e),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )
    
    # Empty state
    empty_state = ft.Column(
        controls=[
            ft.Icon(ft.Icons.HUB_OUTLINED, size=64, color=Colors.TEXT_MUTED),
            ft.Container(height=16),
            ft.Text("Knowledge Graph", size=20, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
            ft.Container(height=8),
            ft.Text(
                "Visualize connections between concepts you've learned",
                size=14,
                color=Colors.TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=24),
            ft.FilledButton(
                text="Generate Graph",
                icon=ft.Icons.AUTO_GRAPH_ROUNDED,
                style=ft.ButtonStyle(bgcolor=Colors.TEXT_PRIMARY, color=Colors.BG_PRIMARY),
                on_click=lambda e: generate_graph(e),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    def open_graph():
        """Open graph in browser."""
        if GRAPH_HTML_PATH.exists():
            webbrowser.open(GRAPH_HTML_PATH.absolute().as_uri())
    
    async def build_graph():
        """Build rich knowledge graph from learning data with AI-generated relationships."""
        try:
            import sys
            import json
            import re
            pyvis_path = "E:/baoke/pyvis-master"
            if pyvis_path not in sys.path:
                sys.path.insert(0, pyvis_path)
            
            from pyvis.network import Network
            from db.dao import ReceiptDAO, MasteryDAO, EvidenceDAO
            from services.gemini_service import create_gemini_service
            
            # Create network (disable menus to avoid local lib dependency)
            net = Network(
                height="900px",
                width="100%",
                bgcolor="#0a0a1a",
                font_color="#ffffff",
                directed=True,
                heading="Chronos Knowledge Graph",
                select_menu=False,
                filter_menu=False,
                cdn_resources="remote",
            )
            
            # Configure physics for better layout
            net.set_options("""
            {
                "nodes": {
                    "borderWidth": 2,
                    "shadow": true,
                    "font": {"size": 14, "face": "Arial"}
                },
                "edges": {
                    "color": {"inherit": "both"},
                    "smooth": {"type": "continuous"},
                    "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}}
                },
                "physics": {
                    "barnesHut": {
                        "gravitationalConstant": -8000,
                        "centralGravity": 0.1,
                        "springLength": 200,
                        "springConstant": 0.04
                    },
                    "stabilization": {"iterations": 150}
                },
                "interaction": {
                    "hover": true,
                    "tooltipDelay": 200,
                    "navigationButtons": true
                }
            }
            """)
            
            # Get all learning data
            receipts = await ReceiptDAO.list_recent(limit=30)
            mastery_data = await MasteryDAO.list_all()
            evidence_data = await EvidenceDAO.list_recent(limit=50)
            
            # Collect all concepts
            all_concepts = []
            concept_details = {}
            
            # Extract topics from receipts
            for receipt in receipts:
                topics = receipt.get("topics_json", [])
                if isinstance(topics, str):
                    try:
                        topics = json.loads(topics)
                    except:
                        topics = [topics] if topics else []
                
                for topic in topics[:5]:
                    topic_clean = str(topic).strip()[:40]
                    if topic_clean and topic_clean not in concept_details:
                        all_concepts.append(topic_clean)
                        concept_details[topic_clean] = {
                            "type": "topic",
                            "source": "session",
                            "summary": receipt.get("summary", "")[:100]
                        }
            
            # Extract from mastery
            for item in mastery_data[:15]:
                concept = item.get("concept", "")[:40]
                level = item.get("level", 0)
                if concept and concept not in concept_details:
                    all_concepts.append(concept)
                    concept_details[concept] = {
                        "type": "mastery",
                        "level": level,
                        "source": "mastery"
                    }
            
            # If no data, use demo data
            if not all_concepts:
                print("No data found, using demo data for Knowledge Graph")
                demo_data = [
                    ("Python Basics", "topic", 0.9, "Core programming fundamentals"),
                    ("Variables & Types", "topic", 0.85, "Data types and variables"),
                    ("Functions", "topic", 0.75, "Defining and using functions"),
                    ("Loops", "mastery", 0.8, "For and while loops"),
                    ("Conditionals", "mastery", 0.7, "If-else statements"),
                    ("Lists", "topic", 0.65, "List operations"),
                    ("Dictionaries", "topic", 0.6, "Key-value pairs"),
                    ("Classes", "mastery", 0.5, "Object-oriented programming"),
                    ("Inheritance", "mastery", 0.4, "Class inheritance"),
                    ("Recursion", "topic", 0.35, "Recursive algorithms"),
                    ("File I/O", "topic", 0.55, "Reading and writing files"),
                    ("Error Handling", "mastery", 0.45, "Try-except blocks"),
                ]
                for name, ctype, level, summary in demo_data:
                    all_concepts.append(name)
                    concept_details[name] = {
                        "type": ctype,
                        "level": level,
                        "source": "demo",
                        "summary": summary
                    }
            
            # Use Gemini to generate concept relationships
            relationships = []
            if all_concepts and len(all_concepts) >= 2:
                try:
                    service = create_gemini_service()
                    if service:
                        concepts_list = ", ".join(all_concepts[:20])
                        prompt = f"""Analyze these learning concepts and generate relationships between them.

Concepts: {concepts_list}

For each pair of related concepts, output a relationship in this JSON format:
[
  {{"from": "concept1", "to": "concept2", "relation": "is-prerequisite-for|extends|related-to|part-of", "label": "short label"}},
  ...
]

Rules:
- Only include meaningful relationships
- Maximum 15 relationships
- Use exact concept names from the list
- Return ONLY valid JSON array

Output:"""
                        
                        response = await service.send_message(prompt)
                        match = re.search(r'\[[\s\S]*\]', response)
                        if match:
                            relationships = json.loads(match.group())[:15]
                            print(f"AI generated {len(relationships)} relationships")
                except Exception as ex:
                    print(f"AI relationship generation skipped: {ex}")
            
            # Track added nodes
            added_nodes = set()
            edge_count = 0
            
            # Add category nodes (hubs)
            categories = [
                ("[Topics]", "#3B82F6", "Topics from learning sessions"),
                ("[Skills]", "#22C55E", "Skills and mastery levels"),
                ("[Concepts]", "#F59E0B", "Key concepts discovered"),
            ]
            
            for cat_id, color, desc in categories:
                net.add_node(
                    cat_id,
                    label=cat_id,
                    color=color,
                    size=35,
                    shape="diamond",
                    title=desc,
                    font={"size": 16, "color": "#ffffff", "bold": True},
                )
                added_nodes.add(cat_id)
            
            # Add concept nodes
            for concept in all_concepts[:25]:
                if concept in added_nodes:
                    continue
                
                details = concept_details.get(concept, {})
                
                # Determine node properties based on type
                if details.get("type") == "mastery":
                    level = details.get("level", 0)
                    if level >= 0.8:
                        color = "#22C55E"
                        border = "#16A34A"
                    elif level >= 0.5:
                        color = "#F59E0B"
                        border = "#D97706"
                    else:
                        color = "#EF4444"
                        border = "#DC2626"
                    
                    size = 18 + int(level * 12)
                    shape = "dot"
                    title = f"Skill: {concept}\nMastery: {int(level * 100)}%"
                    parent = "[Skills]"
                else:
                    color = "#6366F1"
                    border = "#4F46E5"
                    size = 20
                    shape = "dot"
                    title = f"Topic: {concept}\n{details.get('summary', '')[:80]}"
                    parent = "[Topics]"
                
                net.add_node(
                    concept,
                    label=concept[:25],
                    color={"background": color, "border": border},
                    size=size,
                    shape=shape,
                    title=title,
                )
                added_nodes.add(concept)
                
                # Connect to parent category
                net.add_edge(parent, concept, color=f"{color}60", width=1)
                edge_count += 1
            
            # Add AI-generated relationships
            relation_colors = {
                "is-prerequisite-for": "#EF4444",
                "extends": "#22C55E",
                "related-to": "#3B82F6",
                "part-of": "#F59E0B",
            }
            
            for rel in relationships:
                from_node = rel.get("from", "")
                to_node = rel.get("to", "")
                relation = rel.get("relation", "related-to")
                label = rel.get("label", "")
                
                if from_node in added_nodes and to_node in added_nodes:
                    color = relation_colors.get(relation, "#8B5CF6")
                    net.add_edge(
                        from_node,
                        to_node,
                        color=color,
                        title=label,
                        label=label[:15] if label else "",
                        width=2,
                        dashes=relation == "related-to",
                    )
                    edge_count += 1
            
            # Add some cross-category connections for visual interest
            topic_nodes = [c for c in all_concepts[:10] if concept_details.get(c, {}).get("type") == "topic"]
            skill_nodes = [c for c in all_concepts[:10] if concept_details.get(c, {}).get("type") == "mastery"]
            
            for i, topic in enumerate(topic_nodes[:3]):
                for skill in skill_nodes[i:i+2]:
                    if topic in added_nodes and skill in added_nodes:
                        net.add_edge(topic, skill, color="#ffffff20", width=1, dashes=True)
                        edge_count += 1
            
            # Save graph (use CDN resources, not local)
            GRAPH_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
            net.write_html(str(GRAPH_HTML_PATH), local=False, notebook=False)
            
            state["node_count"] = len(added_nodes)
            state["edge_count"] = edge_count
            
            return True
            
        except Exception as e:
            print(f"Graph generation error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_ui():
        """Update UI based on state."""
        if state["graph_generated"]:
            loading.visible = False
            empty_state.visible = False
            success_state.visible = True
            status_text.value = f"{state['node_count']} nodes, {state['edge_count']} edges"
        else:
            loading.visible = False
            empty_state.visible = True
            success_state.visible = False
        
        if state["page"]:
            state["page"].update()
    
    async def do_generate():
        """Async graph generation."""
        loading.visible = True
        empty_state.visible = False
        success_state.visible = False
        if state["page"]:
            state["page"].update()
        
        success = await build_graph()
        state["graph_generated"] = success
        update_ui()
        
        # Auto open in browser
        if success:
            open_graph()
    
    def generate_graph(e):
        """Handle generate button click."""
        if state["page"] is None:
            if hasattr(e, "page"):
                state["page"] = e.page
            elif hasattr(e, "control") and hasattr(e.control, "page"):
                state["page"] = e.control.page
        
        if state["page"]:
            state["page"].run_task(do_generate)
    
    return ft.Container(
        content=ft.Column(
            controls=[
                # Header
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("Knowledge Graph", size=20, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                            ft.Container(expand=True),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=24, vertical=16),
                ),
                # Content
                ft.Container(
                    content=ft.Stack(
                        controls=[
                            ft.Container(
                                content=loading,
                                alignment=ft.alignment.center,
                                expand=True,
                            ),
                            ft.Container(
                                content=success_state,
                                alignment=ft.alignment.center,
                                expand=True,
                            ),
                            ft.Container(
                                content=empty_state,
                                alignment=ft.alignment.center,
                                expand=True,
                            ),
                        ],
                    ),
                    expand=True,
                    padding=ft.padding.only(left=24, right=24, bottom=24),
                ),
            ],
        ),
        expand=True,
        bgcolor=Colors.BG_PRIMARY,
    )
