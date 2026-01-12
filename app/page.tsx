import MainView from "@/components/MainView";

export default function Home() {
  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col items-center p-4">
      <div className="max-w-4xl w-full space-y-8">
        <header className="py-8 text-center border-b border-neutral-800">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-2">
            AutoClip
          </h1>
          <p className="text-neutral-400">
            Automated Video Clipping & Social Prep. No server, no fees.
          </p>
        </header>
        <MainView />
      </div>
    </main>
  );
}
