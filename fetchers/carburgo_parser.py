# Dashboard 2.0 Design Specification: "Ceramic Future"

## Core Concept
A "Clean & Futuristic" aesthetic that avoids "gamer/neon" tropes. Think **Apple Vision Pro** meets **Linear.app**.
- **Theme:** Light/Ceramic (High-end, professional, airy).
- **Key Visuals:** Glassmorphism, subtle gradients, micro-interactions, sophisticated typography.

## Typography
- **Primary Font:** `Outfit` (Google Fonts) - Geometric, modern, clean.
- **Weights:** Light (300) for labels, Medium (500) for body, Bold (700) for numbers.

## Color Palette
- **Background:** `bg-zinc-50` (Subtle warm grey)
- **Surface:** `bg-white/80` with `backdrop-blur-xl` (Frosted glass)
- **Borders:** `border-white/20` (Subtle highlight)
- **Text:**
  - Primary: `text-zinc-900` (Deep black)
  - Secondary: `text-zinc-500` (Medium grey)
- **Accents:**
  - Primary: `violet-600` (Modern tech feel)
  - Success: `emerald-500` (Clean green)
  - Warning: `amber-500` (Warm yellow)
  - Danger: `rose-500` (Soft red)

## Layout Structure
1.  **Floating Sidebar:** A glass rail on the left, detached from the edge.
2.  **Bento Grid:** A fluid grid for metrics, allowing cards to span different sizes.
3.  **Sectioning:**
    - **Header:** Greeting + Global Filters (Date).
    - **Overview Row:** 3 Key Metric Cards (Leads, Visits, Sales).
    - **Charts Row:** 3 Pie Charts (Channel, Origin, Seller).
    - **Deep Dive Row:** Sales Ranking (Left) + Loss Reasons (Right).

## Data Mapping (Must Include ALL)
1.  **Central de Leads:** Total Leads + Breakdown (Waiting, In Progress, Finished).
2.  **Agendamentos:** Scheduled + Breakdown (Completed, Missed, Rate).
3.  **Vendas:** Closed Deals + Breakdown (Negotiating, Lost, Conversion Rate).
4.  **Charts:** Leads by Channel, Origin, Seller.
5.  **Rankings:** Sales Ranking (User, Sales, Value) + Loss Reasons.

## Component Style: "The Glass Card"
```css
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.05);
  border-radius: 24px;
}
