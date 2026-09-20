#include <array>
#include <cmath>
#include <iostream>
#include <cassert>
int main(){
 std::array<int,10> counts{}; counts[0]=128; for(int i=1;i<=9;i++)counts[i]=32; int total=416;
 double pp=0,pb=0,ptie=0;
 auto settle=[&](int p,int b,double q){p%=10;b%=10;if(p>b)pp+=q;else if(b>p)pb+=q;else ptie+=q;};
 auto bd=[](int b,int t){if(b<=2)return true;if(b==3)return t!=8;if(b==4)return t>=2&&t<=7;if(b==5)return t>=4&&t<=7;if(b==6)return t==6||t==7;return false;};
 auto each=[](auto& deck,int rem,auto&& fn){for(int v=0;v<=9;v++){if(deck[v]<=0)continue;double p=(double)deck[v]/rem;--deck[v];fn(v,p);++deck[v];}};
 auto deck=counts;
 each(deck,total,[&](int p1,double q1){each(deck,total-1,[&](int b1,double q2){each(deck,total-2,[&](int p2,double q3){each(deck,total-3,[&](int b2,double q4){double base=q1*q2*q3*q4;int p=(p1+p2)%10,b=(b1+b2)%10;if(p>=8||b>=8){settle(p,b,base);return;}if(p<=5){each(deck,total-4,[&](int p3,double q5){double p5=base*q5;int pf=(p+p3)%10;if(bd(b,p3)){each(deck,total-5,[&](int b3,double q6){settle(pf,(b+b3)%10,p5*q6);});}else settle(pf,b,p5);});}else{if(b<=5){each(deck,total-4,[&](int b3,double q5){settle(p,(b+b3)%10,base*q5);});}else settle(p,b,base);}});});});});
 double sum=pp+pb+ptie;pp/=sum;pb/=sum;ptie/=sum;
 std::cout<<pp<<" "<<pb<<" "<<ptie<<"\n";
 double pev=pp-pb, bev=0.95*pb-pp;
 std::cout<<"playerEV "<<pev<<" bankerEV "<<bev<<"\n";
 assert(std::abs(pev - (-0.0123508)) < 0.00002);
 assert(std::abs(bev - (-0.0105791)) < 0.00002);
}
