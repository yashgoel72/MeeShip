import { Link } from 'react-router-dom'
import Layout from '../components/Layout'

export default function RefundPage() {
  return (
    <Layout>
      <div className="mx-auto max-w-3xl px-4 pt-28 pb-16">
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

        <article className="prose prose-slate max-w-none">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
            Refund & Cancellation Policy
          </h1>
          
          <p className="text-sm text-slate-500">
            Last updated: January 20, 2026
          </p>

          <p>
            We want you to be satisfied with MeeShip. This policy explains our refund and 
            cancellation terms for credit pack purchases.
          </p>

          <h2>1. Credit Pack Purchases</h2>
          <p>
            MeeShip operates on a prepaid credit system. Once credits are added to your account 
            after successful payment verification, they are generally non-refundable as they 
            represent a digital service that can be consumed immediately.
          </p>

          <h2>2. Refund Eligibility</h2>
          
          <div className="rounded-2xl bg-emerald-50 p-4 not-prose mb-6">
            <h3 className="font-semibold text-emerald-900 mb-2">✅ Refunds ARE available for:</h3>
            <ul className="text-sm text-emerald-800 space-y-2">
              <li>• <strong>Double/Duplicate Charges:</strong> If you were charged multiple times for the same purchase</li>
              <li>• <strong>Technical Failures:</strong> If payment was deducted but credits were not added due to a system error</li>
              <li>• <strong>Service Unavailability:</strong> If the service is unavailable for an extended period (more than 48 hours) preventing you from using purchased credits</li>
            </ul>
          </div>

          <div className="rounded-2xl bg-rose-50 p-4 not-prose mb-6">
            <h3 className="font-semibold text-rose-900 mb-2">❌ Refunds are NOT available for:</h3>
            <ul className="text-sm text-rose-800 space-y-2">
              <li>• Credits that have already been used (partially or fully)</li>
              <li>• Change of mind after purchase</li>
              <li>• Dissatisfaction with AI-generated results (as results vary based on input image quality)</li>
              <li>• Expired credits due to non-use within validity period</li>
              <li>• Trial/Starter packs (7-day validity packs)</li>
            </ul>
          </div>

          <h2>3. Pack-Specific Policies</h2>
          
          <table>
            <thead>
              <tr>
                <th>Pack</th>
                <th>Validity</th>
                <th>Refund Policy</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>MeeShip Trial (₹99)</td>
                <td>7 days</td>
                <td>Non-refundable (except technical failures)</td>
              </tr>
              <tr>
                <td>MeeShip Pro (₹499)</td>
                <td>30 days</td>
                <td>Refundable only for double-charge or technical failure within 7 days of purchase</td>
              </tr>
              <tr>
                <td>MeeShip Max (₹999)</td>
                <td>90 days</td>
                <td>Refundable only for double-charge or technical failure within 7 days of purchase</td>
              </tr>
            </tbody>
          </table>

          <h2>4. How to Request a Refund</h2>
          <ol>
            <li>Email us at <a href="mailto:meeship.seller@gmail.com" className="text-meesho hover:underline">meeship.seller@gmail.com</a> with subject line "Refund Request"</li>
            <li>Include your registered email address and order/transaction ID</li>
            <li>Describe the issue (double charge, technical failure, etc.)</li>
            <li>Attach any supporting screenshots if available</li>
          </ol>

          <h2>5. Refund Processing</h2>
          <p>
            We aim to review all refund requests within <strong>3-5 business days</strong>. If approved:
          </p>
          <ul>
            <li>Refunds are processed through Razorpay to the original payment method</li>
            <li>Bank processing may take an additional 5-7 business days</li>
            <li>You will receive email confirmation once the refund is initiated</li>
          </ul>

          <h2>6. Cancellation</h2>
          <p>
            MeeShip is a prepaid service without recurring subscriptions. There is no 
            auto-renewal—you purchase credits as needed. Therefore, there is no cancellation 
            process required. Simply stop purchasing new credit packs when you no longer 
            wish to use the service.
          </p>

          <h2>7. Contact</h2>
          <p>
            For refund requests or questions about this policy, contact us at{' '}
            <a href="mailto:meeship.seller@gmail.com" className="text-meesho hover:underline">
              meeship.seller@gmail.com
            </a>
          </p>
          <p className="text-sm text-slate-500">
            Response time: Within 24-48 hours (Mon-Sat, 10 AM - 6 PM IST)
          </p>
        </article>
      </div>
    </Layout>
  )
}
