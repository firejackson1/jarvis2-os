// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <algorithm>
#include <vector>
namespace jarvis2 {
struct LcarsTile { int index, x, y, w, h; };
struct LcarsGeometry {
  int columns=1, margin=0, rail=0, header_bottom=0, footer_top=0;
  std::vector<LcarsTile> tiles;
};
enum class Direction { Up, Down, Left, Right };
inline int LcarsStep(int selected, int count, int columns, Direction direction) {
  if (count<=0 || columns<=0) return -1;
  selected=std::clamp(selected,0,count-1);
  switch(direction) {
    case Direction::Up: return std::max(0,selected-columns);
    case Direction::Down: return std::min(count-1,selected+columns);
    case Direction::Left: return selected%columns ? selected-1 : selected;
    case Direction::Right: return selected%columns+1<columns ? std::min(count-1,selected+1) : selected;
  }
  return selected;
}
inline LcarsGeometry LcarsLayout(int width,int height,int char_width,int char_height,int count,int selected,int header_lines=1) {
  LcarsGeometry g;
  if(width<=0 || height<=0 || char_width<=0 || char_height<=0 || count<=0) return g;
  g.margin=std::max(12,width/40);
  g.rail=width>=640 ? width/8 : 0;
  int gap=std::max(12,char_height/2);
  int left=g.margin+g.rail+gap, available=width-left-g.margin;
  g.columns=available>=char_width*36 ? 2 : 1;
  g.header_bottom=g.margin+char_height*(3+std::max(1,header_lines));
  g.footer_top=height-g.margin-char_height*2;
  int tile_height=char_height*3, tile_width=(available-gap*(g.columns-1))/g.columns;
  int rows=(g.footer_top-g.header_bottom+gap)/(tile_height+gap);
  if(rows<=0 || tile_width<char_width*4) return g;
  int capacity=rows*g.columns;
  selected=std::clamp(selected,0,count-1);
  int first=selected/capacity*capacity;
  for(int i=first;i<std::min(count,first+capacity);++i) {
    int local=i-first;
    g.tiles.push_back({i,left+(local%g.columns)*(tile_width+gap),g.header_bottom+(local/g.columns)*(tile_height+gap),tile_width,tile_height});
  }
  return g;
}
} // namespace jarvis2
