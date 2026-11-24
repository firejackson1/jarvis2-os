// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <recovery_ui/screen_ui.h>
#include <utility>
#include <optional>
#include "lcars_layout.h"
namespace jarvis2 {
inline std::string LcarsClip(const std::string& text,int limit) {
  if(limit<=0)return {};
  if(text.size()<=static_cast<size_t>(limit))return text;
  if(limit<=3)return std::string(limit,'.');
  size_t end=limit-3;
  while(end && (static_cast<unsigned char>(text[end])&0xc0)==0x80)--end;
  return text.substr(0,end)+"...";
}
class LcarsMenu final:public Menu {
 public:
  LcarsMenu(std::vector<std::string> headers,std::vector<std::string> items,size_t selected,
            const DrawInterface& draw,int width,int height,bool main=false)
    :Menu(selected,draw),headers_(std::move(headers)),items_(std::move(items)),width_(width),height_(height),main_(main) {
    selection_=items_.empty() ? -1 : std::min(selected,items_.size()-1);
  }
  int Select(int value)override{
    if(items_.empty())return selection_=-1;
    int offset=main_?0:1, count=items_.size()+offset;
    if(direction_){value=LcarsStep(selection_+offset,count,Geometry().columns,*direction_)-offset;direction_.reset();}
    selection_=(((value+offset)%count)+count)%count-offset;return selection_;
  }
  int SelectVisible(int value)override{
    auto g=Geometry();if(g.tiles.empty()||value<0||value>=static_cast<int>(g.tiles.size()))return selection_;
    return Select(LogicalIndex(g.tiles[value].index));
  }
  int Scroll(int direction)override{return Select(selection_+direction);}
  size_t ItemsCount()const override{return items_.size();}
  bool IsMain()const override{return main_;}
  int LogicalIndex(int displayed)const{return displayed-(main_?0:1);}
  void SetDirection(Direction direction){direction_=direction;}
  void SetMenuHeight(int)override{} // Screen geometry is supplied by the owning UI.
  LcarsGeometry Geometry()const{return LcarsLayout(width_,height_,draw_funcs_.MenuCharWidth(),draw_funcs_.MenuCharHeight(),items_.size()+(main_?0:1),selection_+(main_?0:1),headers_.size());}
  bool CanRender() const {
    int cw=draw_funcs_.MenuCharWidth(), margin=std::max(12,width_/40);
    if(cw<=0 || Geometry().tiles.empty())return false;
    for(const auto& h:headers_)if(h.size()>static_cast<size_t>((width_-2*margin)/cw))return false;
    return true;
  }
  int DrawHeader(int,int)const override{
    int margin=std::max(12,width_/40),ch=draw_funcs_.MenuCharHeight(),cw=draw_funcs_.MenuCharWidth();
    draw_funcs_.SetColor(UIElement::HEADER);draw_funcs_.DrawFill(margin,margin,std::max(1,width_-2*margin),std::max(4,ch/3));
    draw_funcs_.SetColor(UIElement::MENU);draw_funcs_.DrawTextLine(margin,margin+ch,LcarsClip("JARVIS2 // RECOVERY",(width_-2*margin)/cw),true);
    draw_funcs_.SetColor(UIElement::INFO);
    for(size_t i=0;i<headers_.size();++i)draw_funcs_.DrawTextLine(margin,margin+ch*(2+i),LcarsClip(headers_[i],(width_-2*margin)/cw),false);
    return margin+ch*4;
  }
  int DrawItems(int,int,int,bool held)const override{
    auto g=Geometry();int ch=draw_funcs_.MenuCharHeight(),cw=draw_funcs_.MenuCharWidth();
    if(g.tiles.empty())return 0;
    if(g.rail){draw_funcs_.SetColor(UIElement::HEADER);draw_funcs_.DrawFill(g.margin,g.header_bottom,g.rail-cw/2,g.footer_top-g.header_bottom);}
    for(const auto&t:g.tiles){
      int logical=LogicalIndex(t.index);bool selected=logical==selection_;
      draw_funcs_.SetColor(selected?(held?UIElement::MENU_SEL_BG_ACTIVE:UIElement::MENU_SEL_BG):UIElement::MENU_BG);
      draw_funcs_.DrawFill(t.x,t.y,t.w,t.h);
      draw_funcs_.SetColor(UIElement::HEADER);draw_funcs_.DrawFill(t.x,t.y,std::max(4,cw/3),t.h);
      draw_funcs_.SetColor(selected?UIElement::MENU_SEL_FG:UIElement::MENU);
      std::string label=logical<0?"Back":std::to_string(logical+1)+" / "+items_[logical];
      draw_funcs_.DrawTextLine(t.x+cw,t.y+ch,LcarsClip(label,(t.w-2*cw)/cw),selected);
    }
    draw_funcs_.SetColor(UIElement::INFO);
    draw_funcs_.DrawTextLine(g.margin,g.footer_top,LcarsClip("Tap: next   Hold: select   Arrows: move   Enter: select",(width_-2*g.margin)/cw),false);
    return g.footer_top-g.header_bottom;
  }
 private:
  std::vector<std::string> headers_,items_;int width_,height_;bool main_;std::optional<Direction> direction_;
};
} // namespace jarvis2
