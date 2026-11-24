// SPDX-License-Identifier: Apache-2.0
#include <cassert>
#include <iostream>
#include "recovery/lcars_menu.h"
Menu::Menu(size_t n,const DrawInterface& d):selection_(n),draw_funcs_(d){}
int Menu::selection() const{return selection_;}
struct RecordingDraw:DrawInterface {
  mutable int fills=0,texts=0; int width=1280,height=720;
  void SetColor(UIElement)const override{}
  void DrawHighlightBar(int,int,int,int)const override{}
  int DrawHorizontalRule(int)const override{return 0;}
  void DrawScrollBar(int,int)const override{}
  int DrawTextLine(int x,int y,const std::string& s,bool)const override {assert(x>=0&&y>=0&&x+int(s.size())*20<=width&&y+30<=height);++texts;return 30;}
  void DrawSurface(const GRSurface*,int,int,int,int,int,int)const override{}
  void DrawFill(int x,int y,int w,int h)const override {assert(x>=0&&y>=0&&w>=0&&h>=0&&x+w<=width&&y+h<=height);++fills;}
  void DrawTextIcon(int,int,const GRSurface*)const override{}
  int DrawTextLines(int,int,const std::vector<std::string>&)const override{return 0;}
  int DrawWrappedTextLines(int,int,const std::vector<std::string>&)const override{return 0;}
  int MenuCharHeight()const override{return 30;} int MenuCharWidth()const override{return 20;}
  int MenuItemPadding()const override{return 30;} int MenuItemSpacing()const override{return 0;} int MenuItemHeight()const override{return 90;}
};
int main(){
 RecordingDraw d;
 jarvis2::LcarsMenu menu({"Offline build - not hardware tested"},{"Reboot system now",std::string(300,'x'),"Diagnostics","Reboot bootloader","Power off"},0,d,1280,720);
 assert(menu.CanRender());assert(menu.ItemsCount()==5);assert(menu.Select(4)==4);assert(menu.Select(5)==-1);assert(menu.Select(-1)==-1);
 menu.DrawHeader(0,0);menu.DrawItems(0,0,1280,false);assert(d.fills>0&&d.texts>0);
 assert(menu.SelectVisible(2)==1);assert(menu.Scroll(1)==2);assert(!menu.IsMain());
 assert(menu.Select(5)==-1); // the box button must be able to reach Back
 menu.SetDirection(jarvis2::Direction::Right);int core_selected=menu.Select(0);
 assert(core_selected==0 && core_selected==menu.selection());
 menu.SetDirection(jarvis2::Direction::Down);core_selected=menu.Select(core_selected+1);
 assert(core_selected==2 && core_selected==menu.selection());
 menu.SetDirection(jarvis2::Direction::Up);core_selected=menu.Select(core_selected+1);
 assert(core_selected==0 && core_selected==menu.selection());
 jarvis2::LcarsMenu main_menu({}, {"Android","Diagnostics"},0,d,1280,720,true);assert(main_menu.IsMain());assert(main_menu.Select(2)==0);
 jarvis2::LcarsMenu warning({std::string(400,'x')},{"Cancel","Continue"},0,d,1280,720);assert(!warning.CanRender());
 jarvis2::LcarsMenu empty({}, {},0,d,1280,720);assert(empty.Select(1)==-1);empty.DrawHeader(0,0);empty.DrawItems(0,0,1280,false);
 std::cout<<"LCARS menu: actual drawing bounds, long labels, action indexes and empty menus passed\n";
}
