// src/claude_artifacts/color-picker.jsx
import React, { useState, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const ColorPickerArtifact = () => {
  const [color, setColor] = useState('#ff0000');
  const [rgb, setRgb] = useState({ r: 255, g: 0, b: 0 });

  // Convert hex to RGB
  const hexToRgb = useCallback((hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
  }, []);

  // Convert RGB to hex
  const rgbToHex = useCallback((r, g, b) => {
    const toHex = (n) => {
      const hex = Math.round(n).toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    };
    return '#' + toHex(r) + toHex(g) + toHex(b);
  }, []);

  const handleColorChange = useCallback((newColor) => {
    if (typeof newColor === 'string' && /^#[0-9A-F]{6}$/i.test(newColor)) {
      setColor(newColor);
      setRgb(hexToRgb(newColor));
    }
  }, [hexToRgb]);

  const handleRgbChange = useCallback((component, value) => {
    const newRgb = { ...rgb, [component]: value[0] };
    setRgb(newRgb);
    setColor(rgbToHex(newRgb.r, newRgb.g, newRgb.b));
  }, [rgb, rgbToHex]);

  const copyToClipboard = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(color);
    } catch (err) {
      console.error('Failed to copy color:', err);
    }
  }, [color]);

  const presetColors = [
    '#ff0000', '#00ff00', '#0000ff', '#ffff00',
    '#ff00ff', '#00ffff', '#000000', '#ffffff',
    '#ff8800', '#8800ff', '#00ff88', '#888888'
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Color Picker</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label>Preview</Label>
              <div
                className="h-24 w-full rounded-md border cursor-pointer"
                style={{ backgroundColor: color }}
                onClick={copyToClipboard}
                title="Click to copy color"
              />
            </div>

            <div className="space-y-2">
              <Label>Hex Color</Label>
              <div className="flex gap-2">
                <Input 
                  value={color} 
                  onChange={(e) => handleColorChange(e.target.value)}
                  placeholder="#000000"
                  maxLength={7}
                />
                <Button onClick={copyToClipboard} variant="outline" size="sm">
                  Copy
                </Button>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <Label>Red: {rgb.r}</Label>
                <Slider
                  value={[rgb.r]}
                  onValueChange={(value) => handleRgbChange('r', value)}
                  min={0}
                  max={255}
                  step={1}
                  className="mt-2"
                />
              </div>
              
              <div>
                <Label>Green: {rgb.g}</Label>
                <Slider
                  value={[rgb.g]}
                  onValueChange={(value) => handleRgbChange('g', value)}
                  min={0}
                  max={255}
                  step={1}
                  className="mt-2"
                />
              </div>
              
              <div>
                <Label>Blue: {rgb.b}</Label>
                <Slider
                  value={[rgb.b]}
                  onValueChange={(value) => handleRgbChange('b', value)}
                  min={0}
                  max={255}
                  step={1}
                  className="mt-2"
                />
              </div>
            </div>

            <div>
              <Label>Preset Colors</Label>
              <div className="grid grid-cols-6 gap-2 mt-2">
                {presetColors.map((presetColor) => (
                  <button
                    key={presetColor}
                    className="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500 cursor-pointer"
                    style={{ backgroundColor: presetColor }}
                    onClick={() => handleColorChange(presetColor)}
                    title={presetColor}
                  />
                ))}
              </div>
            </div>

            <div className="text-sm text-muted-foreground">
              RGB: {rgb.r}, {rgb.g}, {rgb.b}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ColorPickerArtifact;