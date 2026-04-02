import WhaleStats from "@/components/WhaleStats";
import AlertFeed from "@/components/AlertFeed";
import WhaleList from "@/components/WhaleList";
import NetflowChart from "@/components/NetflowChart";

export default function Home() {
  return (
    <main className="min-h-screen p-6 md:p-12 max-w-[1600px] mx-auto flex flex-col gap-10">
      
      {/* Upper Section: Left Branding & Stats, Right Directory */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-stretch">
        
        {/* Left Side: 60% Width */}
        <div className="lg:col-span-8 flex flex-col justify-center">
          <div className="mb-12 relative">
            <div className="absolute -left-4 top-0 w-1 h-full bg-primary/40 shadow-[0_0_15px_rgba(0,255,163,0.5)]"></div>
            <h1 className="text-6xl font-black tracking-tighter leading-none italic group">
              WHALE<span className="text-primary group-hover:neon-text-green transition-all duration-500">-EYE</span>
            </h1>
            <div className="mt-4 flex items-center gap-4">
              <span className="text-xl font-bold tracking-[0.5em] uppercase text-white/90">
                Web3 巨鲸情报系统
              </span>
              <div className="h-px flex-1 bg-gradient-to-r from-primary/50 to-transparent"></div>
            </div>
            <p className="mt-4 text-xs text-gray-500 font-mono tracking-widest max-w-md uppercase">
              Real-time monitoring of Ethereum mainnet on-chain movements. Advanced intelligence for digital assets.
            </p>
          </div>

          <div className="mt-auto">
            <WhaleStats />
          </div>
        </div>

        {/* Right Side: 40% Width (The Boxed Directory) */}
        <div className="lg:col-span-4 h-full min-h-[500px]">
          <WhaleList />
        </div>
      </section>

      {/* Middle Section: Chart (Full Width Separator) */}
      <section className="relative py-4">
        <div className="absolute top-0 left-0 w-full h-px bg-white/5"></div>
        <div className="pt-6">
          <NetflowChart />
        </div>
        <div className="absolute bottom-0 left-0 w-full h-px bg-white/5"></div>
      </section>

      {/* Bottom Section: Alerts */}
      <section className="flex-1">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 bg-primary"></div>
            <h3 className="text-xs font-bold uppercase tracking-[0.3em] text-gray-400">实时信号流 / Live Signals</h3>
          </div>
          <div className="text-[10px] font-mono text-primary/60 border border-primary/20 px-2 py-0.5 rounded">
            UPDATING: 5S
          </div>
        </div>
        <AlertFeed />
      </section>

      {/* Site Footer Decoration */}
      <footer className="mt-12 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between opacity-40">
        <div className="text-[9px] font-mono tracking-widest uppercase">
          [ SYSTEM LOG: CONNECTION ESTABLISHED // ENCRYPTION AES-256 ]
        </div>
        <div className="flex gap-8 text-[9px] font-bold uppercase tracking-[0.2em]">
          <span>© 2026 Whale-Eye Intel</span>
          <span>Terms of Intelligence</span>
        </div>
      </footer>
    </main>
  );
}
