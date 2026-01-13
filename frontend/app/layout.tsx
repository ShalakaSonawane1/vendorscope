import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { Shield } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VendorScope - AI Vendor Risk Analysis",
  description: "Intelligent vendor risk and due diligence analysis platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
          {/* Navigation */}
          <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center space-x-8">
                  <Link href="/" className="flex items-center space-x-2">
                    <Shield className="h-8 w-8 text-indigo-600" />
                    <span className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent">
                      VendorScope
                    </span>
                  </Link>
                  <div className="hidden md:flex space-x-6">
                    <Link
                      href="/"
                      className="text-gray-700 hover:text-indigo-600 px-3 py-2 text-sm font-medium transition"
                    >
                      Dashboard
                    </Link>
                    <Link
                      href="/vendors"
                      className="text-gray-700 hover:text-indigo-600 px-3 py-2 text-sm font-medium transition"
                    >
                      Vendors
                    </Link>
                    <Link
                      href="/query"
                      className="text-gray-700 hover:text-indigo-600 px-3 py-2 text-sm font-medium transition"
                    >
                      Query
                    </Link>
                    <Link
                      href="/compare"
                      className="text-gray-700 hover:text-indigo-600 px-3 py-2 text-sm font-medium transition"
                    >
                      Compare
                    </Link>
                  </div>
                </div>
                <div className="flex items-center">
                  <Link
                    href="/vendors/add"
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
                  >
                    Add Vendor
                  </Link>
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="mt-12 border-t border-gray-200 bg-white/50 backdrop-blur-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <p className="text-center text-sm text-gray-500">
                VendorScope © 2026 - AI-Powered Vendor Risk Analysis
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}