// Forcing a new Vercel deployment

import Link from "next/link";
import Image from "next/image";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-gray-50 via-white to-indigo-50">
      <header className="w-full shadow-sm bg-white/80 backdrop-blur-md sticky top-0 z-30 transition-all">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center space-x-2 select-none">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-md hover:scale-105 transition-transform duration-200 cursor-pointer">
              CG
            </div>
            <span className="text-xl font-bold text-gray-900 tracking-tight">
              CareerGPT
            </span>
          </div>
          <div className="space-x-3 flex items-center">
            <Link
              href="/login"
              className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-white hover:bg-indigo-500 focus:bg-indigo-600 focus:text-white transition-all duration-150 shadow-sm"
            >
              Log in
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-400 focus:outline-none shadow-md transition-all duration-150"
            >
              Create account
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 via-indigo-500 to-purple-600 animate-gradient-x"></div>
          <div className="pointer-events-none absolute -top-24 -right-24 w-96 h-96 rounded-full bg-purple-400/30 blur-3xl"></div>
          <div className="pointer-events-none absolute -bottom-24 -left-24 w-[28rem] h-[28rem] rounded-full bg-indigo-300/30 blur-3xl"></div>
          <div className="relative max-w-7xl mx-auto px-6 py-24 sm:py-28">
            <div className="max-w-3xl">
              <h1 className="text-4xl sm:text-5xl font-extrabold text-white leading-tight">
                Plan your career, land interviews, and grow faster with AI
              </h1>
              <p className="mt-4 text-base sm:text-lg text-indigo-100">
                Upload your resume, get instant feedback, and chat your way to a
                better job. Personalized guidance, role-specific prep, and
                actionable next steps.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row gap-3">
                <Link
                  href="/chat/new"
                  className="inline-flex items-center justify-center px-5 py-3 rounded-md text-white bg-white/10 hover:bg-white/30 border border-white/20 backdrop-blur-sm shadow-lg transition-all duration-150 active:scale-95 focus:ring-2 focus:ring-white/60"
                >
                  <span className="mr-2">💬</span> Start chatting
                </Link>
                <a
                  href="#features"
                  className="inline-flex items-center justify-center px-5 py-3 rounded-md bg-white text-indigo-700 hover:bg-indigo-50 active:bg-indigo-100 focus:ring-2 focus:ring-indigo-300 shadow transition-all duration-150"
                >
                  <span className="mr-2">✨</span> See features
                </a>
              </div>
            </div>
            {/* How it works */}
            <div className="mt-16">
              <h3 className="text-white/90 text-lg font-semibold">
                How it works
              </h3>
              <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
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
                    className="rounded-xl bg-white/10 border border-white/20 p-5 text-white/90 shadow-md hover:scale-[1.03] hover:shadow-xl transition-transform duration-200 cursor-pointer group"
                  >
                    <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">
                      {step.icon}
                    </div>
                    <div className="text-sm font-semibold group-hover:text-white/100 transition-colors">
                      {step.title}
                    </div>
                    <p className="mt-1 text-sm text-white/80 group-hover:text-white/90 transition-colors">
                      {step.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="bg-white">
          <div className="max-w-7xl mx-auto px-6 py-16 sm:py-20">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">
                Everything you need to move forward
              </h2>
              <p className="mt-3 text-gray-600">
                Built to be clear, fast, and genuinely helpful.
              </p>
            </div>
            <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  icon: "📄",
                  title: "Smart Resume Analysis",
                  desc: "Upload a PDF resume and get concise strengths, gaps, and tailored improvements.",
                  color: "bg-indigo-100 text-indigo-700",
                },
                {
                  icon: "🧭",
                  title: "Personalized Roadmaps",
                  desc: "Ask anything and receive step-by-step plans, resources, and checkpoints for your target role.",
                  color: "bg-purple-100 text-purple-700",
                },
                {
                  icon: "🎯",
                  title: "Interview Prep",
                  desc: "Practice with realistic prompts and receive feedback to sharpen your responses.",
                  color: "bg-pink-100 text-pink-700",
                },
              ].map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-lg hover:scale-[1.03] transition-transform duration-200 cursor-pointer group"
                >
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center text-2xl mb-2 ${feature.color} group-hover:scale-110 transition-transform`}
                  >
                    {feature.icon}
                  </div>
                  <h3 className="mt-2 font-semibold text-gray-900 group-hover:text-indigo-700 transition-colors">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-sm text-gray-600 group-hover:text-gray-800 transition-colors">
                    {feature.desc}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-12 text-center">
              <Link
                href="/register"
                className="inline-flex items-center justify-center px-6 py-3 rounded-md text-white bg-indigo-600 hover:bg-indigo-700 active:scale-95 focus:ring-2 focus:ring-indigo-400 font-medium shadow-lg transition-all duration-150"
              >
                <span className="mr-2">🚀</span> Create your free account
              </Link>
            </div>
            {/* Testimonials */}
            <div className="mt-16">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
                    className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md hover:scale-[1.02] transition-transform duration-200 cursor-pointer group"
                  >
                    <p className="text-sm text-gray-700 group-hover:text-indigo-700 transition-colors">
                      “{t.quote}”
                    </p>
                    <div className="mt-3 text-xs text-gray-500 group-hover:text-gray-800 transition-colors">
                      {t.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* CTA banner */}
            <div className="mt-16 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 p-1">
              <div className="rounded-2xl bg-white p-6 flex flex-col sm:flex-row items-center justify-between shadow-lg">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">
                    Ready to accelerate your career?
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Start a free chat and get personalized help in minutes.
                  </p>
                </div>
                <Link
                  href="/chat/new"
                  className="mt-4 sm:mt-0 inline-flex items-center justify-center px-5 py-2 rounded-md text-white bg-indigo-600 hover:bg-indigo-700 active:scale-95 focus:ring-2 focus:ring-indigo-400 font-medium shadow transition-all duration-150"
                >
                  <span className="mr-2">💬</span> Start free
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-gray-200 bg-white/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-2">
            <Image src="/globe.svg" alt="Globe" width={16} height={16} />
            <span className="font-semibold tracking-tight">CareerGPT</span>
          </div>
          <div className="space-x-4 flex items-center">
            <Link
              href="/login"
              className="hover:text-indigo-700 transition-colors"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="hover:text-indigo-700 transition-colors"
            >
              Register
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
