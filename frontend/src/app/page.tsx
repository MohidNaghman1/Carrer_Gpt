// Forcing a new Vercel deployment

import Link from "next/link";
import Image from "next/image";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-900 via-slate-800 to-blue-900">
      <header className="w-full shadow-md bg-slate-900/90 backdrop-blur-lg sticky top-0 z-30 transition-all border-b border-blue-900/60">
        <div className="max-w-7xl mx-auto px-8 py-6 flex items-center justify-between">
          <div className="flex items-center space-x-3 select-none">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-700 to-blue-900 flex items-center justify-center text-white font-extrabold text-2xl shadow-lg hover:scale-105 transition-transform duration-200 cursor-pointer border-2 border-blue-800/60">
              CG
            </div>
            <span className="text-2xl font-extrabold text-white tracking-tight drop-shadow-sm">
              CareerGPT
            </span>
          </div>
          <div className="space-x-4 flex items-center">
            <Link
              href="/login"
              className="px-5 py-2 text-base font-semibold rounded-xl text-white bg-slate-800 hover:bg-blue-700 focus:bg-blue-800 focus:text-white transition-all duration-150 shadow border border-blue-700/60"
            >
              Log in
            </Link>
            <Link
              href="/register"
              className="px-5 py-2 text-base font-semibold rounded-xl text-white bg-blue-700 hover:bg-blue-800 focus:ring-2 focus:ring-blue-400 focus:outline-none shadow-lg transition-all duration-150"
            >
              Create account
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-slate-900 to-slate-800 animate-gradient-x"></div>
          <div className="pointer-events-none absolute -top-24 -right-24 w-96 h-96 rounded-full bg-blue-700/30 blur-3xl"></div>
          <div className="pointer-events-none absolute -bottom-24 -left-24 w-[28rem] h-[28rem] rounded-full bg-slate-700/30 blur-3xl"></div>
          <div className="relative max-w-7xl mx-auto px-8 py-28 sm:py-32">
            <div className="max-w-3xl bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl p-10 border border-blue-900/30 mx-auto">
              <h1 className="text-5xl sm:text-6xl font-extrabold text-white leading-tight drop-shadow-lg">
                Plan your career, land interviews, and grow faster with AI
              </h1>
              <p className="mt-6 text-lg sm:text-xl text-blue-100 font-medium">
                Upload your resume, get instant feedback, and chat your way to a
                better job. Personalized guidance, role-specific prep, and
                actionable next steps.
              </p>
              <div className="mt-10 flex flex-col sm:flex-row gap-4">
                <Link
                  href="/chat/new"
                  className="inline-flex items-center justify-center px-7 py-3 rounded-2xl text-white bg-blue-700 hover:bg-blue-800 border border-blue-800 shadow-xl transition-all duration-150 active:scale-95 focus:ring-2 focus:ring-blue-400 text-lg font-semibold"
                >
                  <span className="mr-2">💬</span> Start chatting
                </Link>
                <a
                  href="#features"
                  className="inline-flex items-center justify-center px-7 py-3 rounded-2xl bg-white text-blue-800 hover:bg-blue-50 active:bg-blue-100 focus:ring-2 focus:ring-blue-300 shadow-xl transition-all duration-150 text-lg font-semibold"
                >
                  <span className="mr-2">✨</span> See features
                </a>
              </div>
            </div>
            {/* How it works */}
            <div className="mt-20">
              <h3 className="text-white/90 text-2xl font-bold tracking-tight mb-2">
                How it works
              </h3>
              <div className="h-1 w-16 bg-blue-700 rounded-full mb-8"></div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                {[
                  {
                    title: "1. Create a chat",
                    desc: "Start a new session and describe your goal or upload a resume.",
                    icon: "💡",
                  },
                  {
                    title: "2. Get tailored guidance",
                    desc: "Receive concise answers with actionable steps and resources.",
                    icon: "🧭",
                  },
                  {
                    title: "3. Iterate and improve",
                    desc: "Refine your plan, prep for interviews, and track progress.",
                    icon: "🚀",
                  },
                ].map((step, i) => (
                  <div
                    key={step.title}
                    className="rounded-2xl bg-slate-900/80 border border-blue-800 p-7 text-white/90 shadow-lg hover:scale-[1.04] hover:shadow-2xl transition-transform duration-200 cursor-pointer group flex flex-col items-center"
                  >
                    <div className="text-3xl mb-3 group-hover:scale-125 transition-transform">
                      {step.icon}
                    </div>
                    <div className="text-lg font-bold group-hover:text-blue-300 transition-colors mb-1">
                      {step.title}
                    </div>
                    <p className="mt-1 text-base text-blue-100 group-hover:text-white/90 transition-colors text-center">
                      {step.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section
          id="features"
          className="bg-slate-900 border-t border-blue-900/60"
        >
          <div className="max-w-7xl mx-auto px-8 py-20 sm:py-24">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Everything you need to move forward
              </h2>
              <div className="h-1 w-16 bg-blue-700 rounded-full mx-auto my-4"></div>
              <p className="mt-2 text-blue-100 text-lg">
                Built to be clear, fast, and genuinely helpful.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {[
                {
                  icon: "📄",
                  title: "Smart Resume Analysis",
                  desc: "Upload a PDF resume and get concise strengths, gaps, and tailored improvements.",
                  color: "bg-blue-800 text-white",
                },
                {
                  icon: "🧭",
                  title: "Personalized Roadmaps",
                  desc: "Ask anything and receive step-by-step plans, resources, and checkpoints for your target role.",
                  color: "bg-slate-800 text-white",
                },
                {
                  icon: "🎯",
                  title: "Interview Prep",
                  desc: "Practice with realistic prompts and receive feedback to sharpen your responses.",
                  color: "bg-blue-900 text-white",
                },
              ].map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-3xl border border-blue-800 bg-slate-900 p-8 shadow-lg hover:shadow-2xl hover:scale-[1.04] transition-transform duration-200 cursor-pointer group flex flex-col items-center"
                >
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center text-3xl mb-3 ${feature.color} group-hover:scale-125 transition-transform`}
                  >
                    {feature.icon}
                  </div>
                  <h3 className="mt-3 font-bold text-white group-hover:text-blue-300 transition-colors text-lg">
                    {feature.title}
                  </h3>
                  <p className="mt-3 text-base text-blue-100 group-hover:text-white transition-colors text-center">
                    {feature.desc}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-16 text-center">
              <Link
                href="/register"
                className="inline-flex items-center justify-center px-8 py-4 rounded-2xl text-white bg-blue-700 hover:bg-blue-800 active:scale-95 focus:ring-2 focus:ring-blue-400 font-bold shadow-xl text-lg transition-all duration-150"
              >
                <span className="mr-2">🚀</span> Create your free account
              </Link>
            </div>
            {/* Testimonials */}
            <div className="mt-20">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
                {[
                  {
                    quote:
                      "The resume insights were spot on. Got 2 callbacks in a week.",
                    name: "Arjun • Data Analyst",
                  },
                  {
                    quote:
                      "Clear steps and resources made switching to backend so much easier.",
                    name: "Neha • Backend Developer",
                  },
                  {
                    quote:
                      "Practiced with mock questions and felt confident in interviews.",
                    name: "Ravi • SDE 1",
                  },
                ].map((t) => (
                  <div
                    key={t.name}
                    className="rounded-2xl border border-blue-800 bg-slate-900 p-8 shadow-lg hover:shadow-2xl hover:scale-[1.04] transition-transform duration-200 cursor-pointer group flex flex-col items-center"
                  >
                    <p className="text-lg text-blue-100 group-hover:text-white transition-colors text-center">
                      “{t.quote}”
                    </p>
                    <div className="mt-4 text-sm text-blue-200 group-hover:text-white transition-colors">
                      {t.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* CTA banner */}
            <div className="mt-24 rounded-3xl bg-gradient-to-r from-blue-800 to-blue-900 p-1">
              <div className="rounded-3xl bg-slate-900 p-10 flex flex-col sm:flex-row items-center justify-between shadow-2xl">
                <div>
                  <h4 className="text-2xl font-extrabold text-white">
                    Ready to accelerate your career?
                  </h4>
                  <p className="text-lg text-blue-100 mt-2">
                    Start a free chat and get personalized help in minutes.
                  </p>
                </div>
                <Link
                  href="/chat/new"
                  className="mt-6 sm:mt-0 inline-flex items-center justify-center px-8 py-4 rounded-2xl text-white bg-blue-700 hover:bg-blue-800 active:scale-95 focus:ring-2 focus:ring-blue-400 font-bold shadow-xl text-lg transition-all duration-150"
                >
                  <span className="mr-2">💬</span> Start free
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-blue-900 bg-slate-900/95 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-8 py-8 flex items-center justify-between text-base text-blue-100">
          <div className="flex items-center space-x-3">
            <Image src="/globe.svg" alt="Globe" width={20} height={20} />
            <span className="font-extrabold tracking-tight text-white text-lg">
              CareerGPT
            </span>
          </div>
          <div className="space-x-6 flex items-center">
            <Link
              href="/login"
              className="hover:text-white transition-colors font-semibold"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="hover:text-white transition-colors font-semibold"
            >
              Register
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
