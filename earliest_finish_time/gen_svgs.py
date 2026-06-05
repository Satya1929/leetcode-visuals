import os
import svgwrite

COLORS = {
    'blue': '#2563eb',   # active pointer/current item
    'green': '#16a34a',  # best/accepted state
    'amber': '#f59e0b',  # waiting/comparison
    'red': '#ef4444',    # removed/invalid
    'slate': '#475569',  # inactive context
    'panel': '#f8fafc',  # background card
    'text': '#334155',
    'bg': '#ffffff'
}

def create_timeline_svg(filename, timelines, title="Timeline Diagram"):
    dwg = svgwrite.Drawing(filename, size=('800px', '300px'))
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill=COLORS['bg']))
    dwg.add(dwg.text(title, insert=(20, 30), fill=COLORS['text'], font_family='sans-serif', font_size='20px', font_weight='bold'))
    
    y_offset = 80
    row_height = 80
    scale = 30 # pixels per time unit
    
    for row in timelines:
        dwg.add(dwg.text(row['name'], insert=(20, y_offset + 30), fill=COLORS['text'], font_family='sans-serif', font_size='16px'))
        dwg.add(dwg.line(start=(100, y_offset + 40), end=(750, y_offset + 40), stroke=COLORS['slate'], stroke_width=2))
        
        for start, dur, color_key, label in row['intervals']:
            x_start = 100 + start * scale
            width = dur * scale
            color = COLORS.get(color_key, COLORS['blue'])
            
            rect = dwg.rect(insert=(x_start, y_offset + 10), size=(width, 30), rx=5, ry=5, fill=color, opacity=0.8)
            dwg.add(rect)
            
            dwg.add(dwg.text(f"[{start}, {start+dur}]", insert=(x_start + 5, y_offset + 30), fill='#ffffff', font_family='sans-serif', font_size='12px'))
            if label:
                dwg.add(dwg.text(label, insert=(x_start + width/2, y_offset - 5), fill=color, font_family='sans-serif', font_size='14px', font_weight='bold', text_anchor='middle'))
                
        # Draw wait periods if any
        if 'wait' in row:
            for w_start, w_end in row['wait']:
                x1 = 100 + w_start * scale
                x2 = 100 + w_end * scale
                dwg.add(dwg.line(start=(x1, y_offset + 25), end=(x2, y_offset + 25), stroke=COLORS['red'], stroke_width=2, stroke_dasharray="4,4"))
                dwg.add(dwg.text("wait", insert=((x1+x2)/2, y_offset + 20), fill=COLORS['red'], font_family='sans-serif', font_size='12px', text_anchor='middle'))

        y_offset += row_height
        
    dwg.save()
    print(f"Generated {filename}")

if __name__ == "__main__":
    out_dir = os.path.dirname(__file__)
    
    # 1. minL and minW concept
    create_timeline_svg(os.path.join(out_dir, "min_time.svg"), [
        {'name': 'Land', 'intervals': [(2, 3, 'green', 'minL'), (5, 5, 'slate', ''), (8, 2, 'slate', '')]},
        {'name': 'Water', 'intervals': [(3, 4, 'blue', 'minW'), (9, 1, 'slate', '')]}
    ], "Finding Earliest Possible Individual Rides (minL & minW)")
    
    # 2. Scenario 1: Land First, then Water
    create_timeline_svg(os.path.join(out_dir, "scenario1.svg"), [
        {'name': 'Land 1st', 'intervals': [(2, 3, 'green', 'minL')]},
        {'name': 'Water', 'intervals': [(9, 1, 'blue', '')], 'wait': [(5, 9)]}
    ], "Scenario 1: Fastest Land Ride + Later Water Ride")
    
    # 3. Scenario 2: Water First, then Land
    create_timeline_svg(os.path.join(out_dir, "scenario2.svg"), [
        {'name': 'Water 1st', 'intervals': [(3, 4, 'blue', 'minW')]},
        {'name': 'Land', 'intervals': [(8, 2, 'green', '')], 'wait': [(7, 8)]}
    ], "Scenario 2: Fastest Water Ride + Later Land Ride")
