// SPDX-License-Identifier: Apache-2.0
#include <cassert>
#include <iostream>
#include "recovery/lcars_layout.h"
int main() {
  for (auto size : {std::pair<int,int>{640,480}, {1280,720}, {1920,1080}, {3840,2160}}) {
    for (int selected = 0; selected < 23; ++selected) {
      auto g = jarvis2::LcarsLayout(size.first, size.second, size.first/64, size.second/32, 23, selected);
      assert(!g.tiles.empty()); bool visible = false;
      for (const auto& t : g.tiles) {
        assert(t.x >= 0 && t.y >= g.header_bottom);
        assert(t.w > 0 && t.h > 0 && t.x+t.w <= size.first && t.y+t.h <= g.footer_top);
        visible |= t.index == selected;
      }
      assert(visible);
      for (size_t i=0;i<g.tiles.size();++i) for(size_t j=i+1;j<g.tiles.size();++j) {
        const auto&a=g.tiles[i];const auto&b=g.tiles[j];
        assert(a.x+a.w<=b.x || b.x+b.w<=a.x || a.y+a.h<=b.y || b.y+b.h<=a.y);
      }
    }
  }
  assert(jarvis2::LcarsLayout(0,480,10,20,5,0).tiles.empty());
  assert(jarvis2::LcarsLayout(1280,720,20,30,0,0).tiles.empty());
  assert(jarvis2::LcarsLayout(1280,720,20,30,4,999).tiles.back().index==3);
  auto g=jarvis2::LcarsLayout(1280,720,20,30,6,0);
  assert(g.columns==2);
  assert(jarvis2::LcarsStep(0,6,2,jarvis2::Direction::Right)==1);
  assert(jarvis2::LcarsStep(1,6,2,jarvis2::Direction::Down)==3);
  assert(jarvis2::LcarsStep(3,5,2,jarvis2::Direction::Down)==4);
  assert(jarvis2::LcarsStep(0,6,2,jarvis2::Direction::Up)==0);
  assert(jarvis2::LcarsStep(4,5,2,jarvis2::Direction::Right)==4);
  assert(jarvis2::LcarsStep(0,0,2,jarvis2::Direction::Right)==-1);
  std::cout<<"LCARS layout: bounds, pagination, overlap, invalid geometry and spatial navigation passed\n";
}
