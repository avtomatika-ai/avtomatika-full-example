from blueprints import main_bp, metadata_enrichment_bp, maintenance_bp
import os


def generate():
    print("🎨 Generating blueprint graphs...")
    main_bp.render_graph("full_showcase_graph")
    metadata_enrichment_bp.render_graph("metadata_enrichment_graph")
    maintenance_bp.render_graph("periodic_maintenance_graph")
    print(f"✅ Done. Check {os.getcwd()} for .png files.")


if __name__ == "__main__":
    generate()
