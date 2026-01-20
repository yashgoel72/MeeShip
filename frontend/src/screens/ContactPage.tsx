import { useState } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Open mailto link with pre-filled data
    const mailtoLink = `mailto:meeship.seller@gmail.com?subject=${encodeURIComponent(formData.subject || 'Support Request')}&body=${encodeURIComponent(
      `Name: ${formData.name}\nEmail: ${formData.email}\n\nMessage:\n${formData.message}`
    )}`
    window.location.href = mailtoLink
    setSubmitted(true)
  }

  return (
    <Layout>
      <div className="mx-auto max-w-4xl px-4 pt-28 pb-16">
        <div className="mb-8">
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-meesho transition-colors"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </Link>
        </div>

        <div className="text-center mb-12">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
            Contact Us
          </h1>
          <p className="mt-4 text-lg text-slate-600">
            We're here to help! Reach out with any questions about MeeShip.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Contact Information */}
          <div className="space-y-6">
            <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Get in Touch</h2>
              
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-meesho/10 text-meesho">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <div className="font-medium text-slate-900">Email</div>
                    <a 
                      href="mailto:meeship.seller@gmail.com" 
                      className="text-meesho hover:underline"
                    >
                      meeship.seller@gmail.com
                    </a>
                    <p className="mt-1 text-sm text-slate-500">
                      We respond within 24-48 hours
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <div className="font-medium text-slate-900">Business Hours</div>
                    <p className="text-slate-600">Monday - Saturday</p>
                    <p className="text-slate-600">10:00 AM - 6:00 PM IST</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Help */}
            <div className="rounded-2xl bg-slate-50 p-6 ring-1 ring-slate-200">
              <h3 className="font-semibold text-slate-900 mb-3">Common Questions</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/refund" className="text-meesho hover:underline">
                    → Refund & Cancellation Policy
                  </Link>
                </li>
                <li>
                  <Link to="/privacy" className="text-meesho hover:underline">
                    → Privacy & Data Security
                  </Link>
                </li>
                <li>
                  <Link to="/terms" className="text-meesho hover:underline">
                    → Terms of Service
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Contact Form */}
          <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Send us a Message</h2>
            
            {submitted ? (
              <div className="rounded-2xl bg-emerald-50 p-6 text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
                  <svg className="h-6 w-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="font-semibold text-emerald-900">Email Client Opened!</h3>
                <p className="mt-2 text-sm text-emerald-700">
                  Complete sending the email in your mail app.
                </p>
                <button
                  onClick={() => setSubmitted(false)}
                  className="mt-4 text-sm text-emerald-600 hover:underline"
                >
                  Send another message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">
                    Your Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full rounded-xl border-slate-200 px-4 py-3 text-sm ring-1 ring-slate-200 focus:border-meesho focus:ring-meesho"
                    placeholder="Enter your name"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full rounded-xl border-slate-200 px-4 py-3 text-sm ring-1 ring-slate-200 focus:border-meesho focus:ring-meesho"
                    placeholder="your@email.com"
                  />
                </div>

                <div>
                  <label htmlFor="subject" className="block text-sm font-medium text-slate-700 mb-1">
                    Subject
                  </label>
                  <select
                    id="subject"
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    className="w-full rounded-xl border-slate-200 px-4 py-3 text-sm ring-1 ring-slate-200 focus:border-meesho focus:ring-meesho"
                  >
                    <option value="">Select a topic</option>
                    <option value="Payment Issue">Payment Issue</option>
                    <option value="Refund Request">Refund Request</option>
                    <option value="Technical Support">Technical Support</option>
                    <option value="Feature Request">Feature Request</option>
                    <option value="General Inquiry">General Inquiry</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-slate-700 mb-1">
                    Message
                  </label>
                  <textarea
                    id="message"
                    required
                    rows={4}
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    className="w-full rounded-xl border-slate-200 px-4 py-3 text-sm ring-1 ring-slate-200 focus:border-meesho focus:ring-meesho resize-none"
                    placeholder="Describe your question or issue..."
                  />
                </div>

                <button
                  type="submit"
                  className="w-full rounded-2xl bg-meesho px-5 py-3 text-sm font-semibold text-white hover:bg-meesho/90 transition-colors"
                >
                  Send Message
                </button>

                <p className="text-xs text-slate-500 text-center">
                  This will open your email client with the message pre-filled.
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
