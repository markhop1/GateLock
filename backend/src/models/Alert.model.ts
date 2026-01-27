import mongoose, { Schema, Document } from 'mongoose'

export type AlertStatus = 'pending' | 'accepted' | 'ignored' | 'unanswered'

export interface IAlert extends Document {
  personId: mongoose.Types.ObjectId
  personName: string
  videoUrl: string
  message: string
  status: AlertStatus
  userId: mongoose.Types.ObjectId
  timestamp: Date
  decisionTimestamp?: Date
  createdAt: Date
  updatedAt: Date
}

const alertSchema = new Schema<IAlert>(
  {
    personId: {
      type: Schema.Types.ObjectId,
      ref: 'Person',
      required: true,
    },
    personName: {
      type: String,
      required: [true, 'Person name is required'],
      trim: true,
    },
    videoUrl: {
      type: String,
      required: [true, 'Video URL is required'],
      trim: true,
    },
    message: {
      type: String,
      required: [true, 'Message is required'],
      trim: true,
    },
    status: {
      type: String,
      enum: ['pending', 'accepted', 'ignored', 'unanswered'],
      default: 'pending',
      index: true,
    },
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    timestamp: {
      type: Date,
      default: Date.now,
      index: true,
    },
    decisionTimestamp: {
      type: Date,
    },
  },
  {
    timestamps: true,
  }
)

// Indexes for faster queries
alertSchema.index({ userId: 1, status: 1 })
alertSchema.index({ userId: 1, timestamp: -1 })
alertSchema.index({ status: 1, timestamp: 1 })

export const Alert = mongoose.model<IAlert>('Alert', alertSchema)
