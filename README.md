# Library of Ruina Card Data Scraper
Scrap Cards from Tiphereth Database.  
Low burden on database, get almost all data about cards and store them in json files.
## Usage
```bash
git clone https://github.com/TunaFish2K/library-of-ruina-card-data-scraper scraper
cd scraper
pip install -r requirements.txt
```
To scrap combat cards:
```bash
python combat.py
```
Cards will be stored in folder `out/combat`.
## Data Structure
### Combat Card
```typescript
type Card = {
    name: string;
    availability: "collectable" | "obtainable" | "enemy_only";
    type: "melee" | "ranged" | "mass_summation" | "mass_individual" | "immediate";
    rarity: "common" | "uncommon" | "rare" | "unique";
    is_ego: boolean;
    cost: number;
    image: string;
    description: string | null;
    actions: {
        group: "offensive" | "defensive" | "counter";
        type: "pierce" | "slash" | "blunt" | "guard" | "evade";
        min: number;
        max: number;
        description: string | null;
        html_description: string | null;
    }[]
};
```