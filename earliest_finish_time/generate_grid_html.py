import os
import asyncio
from playwright.async_api import async_playwright

BASE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: #262626; display: flex; align-items: flex-start; justify-content: flex-start; padding: 20px; width: max-content; color: #e5e7eb; }
        .frame { display: inline-flex; flex-direction: column; gap: 48px; padding: 32px 48px; background: #262626; border: 1px solid #404040; position: relative;}
        .title { font-size: 1.15rem; font-weight: 800; color: #ffffff; text-align: center; margin-bottom: 24px; text-transform: uppercase; letter-spacing: 0.05em; }
        
        .matrix-container { display: flex; gap: 16px; align-items: flex-end; position: relative; }
        
        .data-table { font-size: 0.85rem; border-collapse: collapse; text-align: center; margin-bottom: 1px; }
        .data-table th { color: #9ca3af; font-weight: 600; padding: 4px 8px; border: none; }
        .data-table th.given { text-align: left; font-style: italic; font-weight: 400; padding-bottom: 8px; }
        .data-table td { padding: 8px; border: 1px solid #525252; color: #d4d4d4; }
        .data-table tr.highlight-row td { color: #4ade80; font-weight: 700; }
        
        .grid-system { display: flex; flex-direction: column; }
        .grid-header { display: grid; margin-bottom: 8px; text-align: center; font-size: 0.85rem; font-weight: 700; color: #d4d4d4; }
        .grid-header-col { display: flex; align-items: center; justify-content: center; }
        .grid-body { display: grid; border: 1px solid #525252; background: #171717; }
        .grid-cell { border-right: 1px solid #404040; border-bottom: 1px solid #404040; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; color: #171717;}
        .grid-row:last-child .grid-cell { border-bottom: none; }
        .grid-cell:last-child { border-right: none; }
        .grid-row { display: contents; }
        
        .block-land { background: #f97316; }
        .block-water { background: #0ea5e9; }
        .block-highlight { background: #4ade80; }
        
        .sync-line { position: absolute; width: 0; border-right: 2px dashed; z-index: 10; }
        .sync-line-land { border-color: #f97316; }
        .sync-line-water { border-color: #0ea5e9; }
        .sync-line-highlight { border-color: #4ade80; }
        
        .legend { font-size: 1.4rem; font-weight: 800; color: #4ade80; text-align: center; margin-top: 16px; }
        .label-side { writing-mode: vertical-rl; transform: rotate(180deg); text-align: center; font-weight: 800; letter-spacing: 0.1em; color: #ffffff; padding-left: 16px; margin-bottom: 1px; }
        
        .side-by-side { display: flex; gap: 64px; }
        .stacked { display: flex; flex-direction: column; gap: 32px; position: relative;}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""

def make_grid_html(title, rides, color_class, label, highlight_idx=-1, hide_table=False, offset_table=False, min_wait=None, single_row=False):
    html = f"""
        <div class="matrix-container">
            <div>
                <table class="data-table" style="{'visibility:hidden' if hide_table else ''}">
                    <tr><th colspan="3" class="given">{"new" if offset_table else "given"}</th></tr>
                    <tr><th>start</th><th>dur</th><th>end</th></tr>
    """
    for i, (s, d, e) in enumerate(rides):
        hl_class = ' class="highlight-row"' if i == highlight_idx else ''
        html += f'                    <tr{hl_class}><td>{s}</td><td>{d}</td><td>{e}</td></tr>\n'
    html += """
                </table>
            </div>
            <div class="grid-system">
                <div class="grid-header" style="grid-template-columns: repeat(10, 32px);">
                    <div class="grid-header-col">1</div><div class="grid-header-col">2</div><div class="grid-header-col">3</div><div class="grid-header-col">4</div><div class="grid-header-col">5</div><div class="grid-header-col">6</div><div class="grid-header-col">7</div><div class="grid-header-col">8</div><div class="grid-header-col">9</div><div class="grid-header-col">10</div>
                </div>
                <div class="grid-body" style="grid-template-columns: repeat(10, 32px); grid-template-rows: repeat(%(rows)s, 32px);">
    """ % {"rows": 1 if single_row else len(rides)}
    for i, (s, d, e) in enumerate(rides):
        html += '                    <div class="grid-row">\n'
        for col in range(1, 11):
            if s <= col < s + d:
                cell_color = "block-highlight" if i == highlight_idx else color_class
                html += f'                        <div class="grid-cell {cell_color}"></div>\n'
            else:
                html += f'                        <div class="grid-cell"></div>\n'
        html += '                    </div>\n'
    html += f"""
                </div>
            </div>
            <div class="label-side">{label}</div>
        </div>
    """
    return html

def make_stacked_frame(title, top_rides, top_label, top_color, bot_rides, bot_label, bot_color, min_val, sync_col1, sync_col2, highlight_top=1):
    content = f"""<div class="frame">
        <div class="title">{title}</div>
        <div class="stacked">
            <div class="sync-line sync-line-{top_color.split('-')[1]}" style="left: calc(138px + {sync_col1 * 32}px); top: -20px; bottom: -20px;"></div>
            <div class="sync-line sync-line-highlight" style="left: calc(138px + {sync_col2 * 32}px); top: -20px; bottom: -20px;"></div>
            
            {make_grid_html('', top_rides, top_color, top_label, highlight_idx=highlight_top)}
            {make_grid_html('', bot_rides, bot_color, bot_label, offset_table=True)}
            
            <div style="display:flex; justify-content:center; margin-top:-16px;">
                <div style="border:1px solid #525252; padding:8px 16px; color:#4ade80; font-weight:800;">min {bot_label} finish = {min_val}</div>
            </div>
        </div>
    </div>"""
    return BASE_HTML.replace("{content}", content)

def make_frame_1(land, water):
    content = f"""<div class="frame side-by-side">
    <div>
        <div class="title">LAND RIDES</div>
        {make_grid_html('', land, 'block-land', 'LAND')}
    </div>
    <div>
        <div class="title">WATER RIDES</div>
        {make_grid_html('', water, 'block-water', 'WATER')}
    </div>
</div>"""
    return BASE_HTML.replace("{content}", content)

def make_frame_2(land):
    content = f"""<div class="frame">
    <div>
        <div class="title">LAND RIDES</div>
        {make_grid_html('', land, 'block-land', 'LAND', highlight_idx=1)}
        <div class="legend">minL = 4</div>
    </div>
</div>"""
    return BASE_HTML.replace("{content}", content)

def make_frame_3(water):
    content = f"""<div class="frame">
    <div>
        <div class="title">WATER RIDES</div>
        {make_grid_html('', water, 'block-water', 'WATER', highlight_idx=4)}
        <div class="legend">minW = 4</div>
    </div>
</div>"""
    return BASE_HTML.replace("{content}", content)

def make_comparison_frame():
    content = f"""<div class="frame side-by-side">
        <div class="stacked">
            <div class="title" style="margin-bottom:0;">SCENARIO A (LAND -> WATER)</div>
            {make_grid_html('', [(3,1,4)], 'block-highlight', 'LAND', highlight_idx=0, single_row=True)}
            {make_grid_html('', [(5,1,6)], 'block-water', 'WATER', single_row=True)}
            <div class="legend" style="color:white; font-size:1.1rem;">Finish: <span style="color:#f97316">6</span></div>
        </div>
        <div class="stacked">
            <div class="title" style="margin-bottom:0;">SCENARIO B (WATER -> LAND)</div>
            {make_grid_html('', [(1,3,4)], 'block-highlight', 'WATER', highlight_idx=0, single_row=True)}
            {make_grid_html('', [(4,1,5)], 'block-land', 'LAND', single_row=True)}
            <div class="legend" style="color:#4ade80; font-size:1.4rem;">Finish: 5 (Minimum)</div>
        </div>
    </div>"""
    return BASE_HTML.replace("{content}", content)

async def capture_screenshots(grids_dir):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use high device scale factor for crisp retina-quality images
        context = await browser.new_context(device_scale_factor=2)
        page = await context.new_page()
        
        for i in range(1, 7):
            html_path = os.path.join(grids_dir, f"frame_{i}.html")
            png_path = os.path.join(grids_dir, f"frame_{i}.png")
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
                
            await page.set_content(html, wait_until='networkidle')
            
            # Wait for Tailwind CDN and fonts to load/render
            await asyncio.sleep(0.5)
            
            container = await page.wait_for_selector('.frame')
            await container.screenshot(path=png_path, omit_background=True)
            print(f"Captured screenshot for frame_{i}.png")
            
        await browser.close()

def main():
    land = [(1,4,5), (3,1,4), (2,2,4), (3,3,6)]
    water = [(6,3,9), (3,5,8), (5,1,6), (3,2,5), (1,3,4)]
    
    grids_dir = r"c:\Users\ASUS\Desktop\Satya\Projects\Leetcode\assets\earliest_finish_time\grids"
    os.makedirs(grids_dir, exist_ok=True)
    
    # Write HTML files
    with open(os.path.join(grids_dir, "frame_1.html"), "w", encoding="utf-8") as f:
        f.write(make_frame_1(land, water))
        
    with open(os.path.join(grids_dir, "frame_2.html"), "w", encoding="utf-8") as f:
        f.write(make_frame_2(land))
        
    with open(os.path.join(grids_dir, "frame_3.html"), "w", encoding="utf-8") as f:
        f.write(make_frame_3(water))
        
    # Scenario A: Land -> Water
    # minL = 4 (land[1] is 3, 1, 4)
    # bot_rides: startW[j] -> max(minL, startW[j])
    updated_water = [(6,3,9), (4,5,9), (5,1,6), (4,2,6), (4,3,7)]
    with open(os.path.join(grids_dir, "frame_4.html"), "w", encoding="utf-8") as f:
        f.write(make_stacked_frame("SCENARIO A: LAND -> WATER", land, "LAND", "block-land", updated_water, "WATER", "block-water", 6, 4, 6, highlight_top=1))
        
    # Scenario B: Water -> Land
    # minW = 4 (water[4] is 1, 3, 4)
    # bot_rides: startL[i] -> max(minW, startL[i])
    updated_land = [(4,4,8), (4,1,5), (4,2,6), (4,3,7)]
    with open(os.path.join(grids_dir, "frame_5.html"), "w", encoding="utf-8") as f:
        f.write(make_stacked_frame("SCENARIO B: WATER -> LAND", water, "WATER", "block-water", updated_land, "LAND", "block-land", 5, 4, 5, highlight_top=4))
        
    with open(os.path.join(grids_dir, "frame_6.html"), "w", encoding="utf-8") as f:
        f.write(make_comparison_frame())
        
    print("HTML files generated. Now capturing screenshots...")
    asyncio.run(capture_screenshots(grids_dir))

if __name__ == "__main__":
    main()
