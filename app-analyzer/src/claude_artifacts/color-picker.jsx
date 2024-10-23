// src/claude_artifacts/color-picker.jsx
import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { ChromePicker } from 'react-color';  // Install this dependency
import { Input } from '@/components/ui/input';

const ColorPickerArtifact = () => {
  const [color, setColor] = useState('#ff0000');

  const handleColorChange = (newColor) => {
    setColor(newColor.hex);
  };

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
                className="h-24 w-full rounded-md border"
                style={{ backgroundColor: color }}
              />
            </div>

            <div className="space-y-2">
              <Label>Hex Color</Label>
              <Input value={color} readOnly />
            </div>

            <ChromePicker
              color={color}
              onChange={handleColorChange}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ColorPickerArtifact;