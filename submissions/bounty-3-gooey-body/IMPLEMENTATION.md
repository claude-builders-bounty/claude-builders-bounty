# 🎮 Gooey Body Upgrade Implementation

## Task Analysis

**Game**: AncientBeast  
**Character**: Gumble  
**Ability**: Gooey Body (Passive)  
**Bounty**: 30 XTR  

## Current Behavior
- Gooey Body leaves a trap on death
- Trap may or may not affect allies
- Hard to check or remember

## Required Upgrade
- Allow Gumble to **leap over units** during moving phase
- Condition: Must walk at least 2 hexagons

## Implementation Approach

### 1. File Structure
```
AncientBeast/
├── src/
│   ├── abilities/
│   │   └── Gumble/
│   │       └── GooeyBody.ts    # Main ability file
│   └── units/
│       └── Gumble.ts           # Unit definition
```

### 2. Core Logic

```typescript
// GooeyBody.ts
class GooeyBody extends PassiveAbility {
  constructor() {
    super({
      name: 'Gooey Body',
      description: 'Gumble can leap over units when moving at least 2 hexagons',
      upgradeLevel: 1
    });
  }

  onMoveStart(unit: Unit, path: Hexagon[]): void {
    // Check if moving at least 2 hexagons
    if (path.length >= 2) {
      // Enable leap mode
      unit.setLeapMode(true);
    }
  }

  canLeapOver(unit: Unit, targetHex: Hexagon): boolean {
    // Check if target hex has a unit
    if (targetHex.hasUnit()) {
      // Allow leaping over
      return true;
    }
    return false;
  }

  onDeath(unit: Unit): void {
    // Keep original trap behavior
    this.createDeathTrap(unit.position);
  }

  private createDeathTrap(position: Hexagon): void {
    // Original trap logic
    const trap = new Trap({
      position,
      effect: 'gooey',
      duration: 2,
      affectsAllies: false // Clarify: only affects enemies
    });
    this.game.addTrap(trap);
  }
}
```

### 3. Movement System Integration

```typescript
// MovementHandler.ts
class MovementHandler {
  calculatePath(
    unit: Unit, 
    from: Hexagon, 
    to: Hexagon
  ): Hexagon[] {
    const path = this.findPath(from, to);
    
    // Check for Gooey Body ability
    if (unit.hasAbility('GooeyBody') && path.length >= 2) {
      // Allow path through occupied hexes
      return this.calculateLeapPath(unit, path);
    }
    
    return path;
  }

  private calculateLeapPath(unit: Unit, path: Hexagon[]): Hexagon[] {
    const leapPath: Hexagon[] = [path[0]]; // Start position
    
    for (let i = 1; i < path.length; i++) {
      const hex = path[i];
      
      // If hex has a unit, check if we can leap over
      if (hex.hasUnit() && hex.unit !== unit) {
        // Can leap over if next hex is free
        if (i + 1 < path.length && !path[i + 1].hasUnit()) {
          leapPath.push(hex); // Land on hex after the unit
          i++; // Skip the next hex (we landed there)
        }
      } else {
        leapPath.push(hex);
      }
    }
    
    return leapPath;
  }
}
```

### 4. Visual Feedback

```typescript
// GooeyBodyVisual.ts
class GooeyBodyVisual extends AbilityVisual {
  onLeapStart(unit: Unit): void {
    // Show leap animation
    this.playAnimation('gooey_leap_start', unit.position);
    
    // Add visual indicator
    this.addIndicator(unit, 'leap_mode_active');
  }

  onLeapOver(unit: Unit, leapedUnit: Unit): void {
    // Show leap arc
    this.playAnimation('gooey_leap_arc', {
      from: unit.position,
      over: leapedUnit.position,
      to: this.getLandingPosition(unit, leapedUnit)
    });
  }

  onDeathTrap(position: Hexagon): void {
    // Original trap visual
    this.spawnTrapVisual(position, 'gooey_puddle');
  }
}
```

### 5. UI Updates

```typescript
// AbilityTooltip.ts
const gooeyBodyTooltip = {
  title: 'Gooey Body',
  description: `
    Passive Ability
    
    ✦ On Death: Leaves a gooey trap that slows enemies
    ✦ On Move (2+ hexes): Can leap over units
    
    Leap: Move through enemy units when walking at least 2 hexagons
  `,
  icon: 'abilities/gooey_body.png',
  upgradeIndicator: true
};
```

## Testing Checklist

- [ ] Gumble can move normally (1 hex)
- [ ] Gumble can leap over units (2+ hexes)
- [ ] Leap only works when path is 2+ hexagons
- [ ] Cannot leap over if landing hex is occupied
- [ ] Death trap still works correctly
- [ ] Trap only affects enemies (not allies)
- [ ] Visual feedback shows leap mode
- [ ] Tooltip explains both effects

## Files to Modify

1. `src/abilities/Gumble/GooeyBody.ts` - Main ability logic
2. `src/movement/MovementHandler.ts` - Pathfinding integration
3. `src/visuals/AbilityVisuals.ts` - Visual effects
4. `src/ui/AbilityTooltip.ts` - Tooltip text

## Notes

- Keep backward compatibility with existing saves
- Ensure leap doesn't break other movement abilities
- Test edge cases (leaping over multiple units, leaping at map edge)
