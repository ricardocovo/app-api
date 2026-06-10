USE [focused-tube]
GO
/****** Object:  Table [dbo].[Profile]    Script Date: 6/9/2026 5:41:34 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Profile](
	[id] [nvarchar](1000) NOT NULL,
	[name] [nvarchar](1000) NOT NULL,
	[userId] [nvarchar](1000) NOT NULL,
	[isDefault] [bit] NOT NULL,
	[createdAt] [datetime2](7) NOT NULL,
	[updatedAt] [datetime2](7) NOT NULL,
	[isPublic] [bit] NOT NULL,
 CONSTRAINT [Profile_pkey] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ProfileChannel]    Script Date: 6/9/2026 5:41:34 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ProfileChannel](
	[id] [nvarchar](1000) NOT NULL,
	[profileId] [nvarchar](1000) NOT NULL,
	[youtubeChannelId] [nvarchar](1000) NOT NULL,
	[channelTitle] [nvarchar](1000) NOT NULL,
	[thumbnailUrl] [nvarchar](1000) NULL,
 CONSTRAINT [ProfileChannel_pkey] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ProfileFollow]    Script Date: 6/9/2026 5:41:34 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ProfileFollow](
	[id] [nvarchar](1000) NOT NULL,
	[followerId] [nvarchar](1000) NOT NULL,
	[profileId] [nvarchar](1000) NOT NULL,
	[createdAt] [datetime2](7) NOT NULL,
 CONSTRAINT [ProfileFollow_pkey] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [ProfileFollow_followerId_profileId_key] UNIQUE NONCLUSTERED 
(
	[followerId] ASC,
	[profileId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ProfileKeyword]    Script Date: 6/9/2026 5:41:34 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ProfileKeyword](
	[id] [nvarchar](1000) NOT NULL,
	[profileId] [nvarchar](1000) NOT NULL,
	[keyword] [nvarchar](1000) NOT NULL,
 CONSTRAINT [ProfileKeyword_pkey] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[User]    Script Date: 6/9/2026 5:41:34 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[User](
	[id] [nvarchar](1000) NOT NULL,
	[googleId] [nvarchar](1000) NOT NULL,
	[email] [nvarchar](1000) NOT NULL,
	[name] [nvarchar](1000) NOT NULL,
	[avatarUrl] [nvarchar](1000) NULL,
	[accessToken] [nvarchar](1000) NOT NULL,
	[refreshToken] [nvarchar](1000) NOT NULL,
	[createdAt] [datetime2](7) NOT NULL,
	[updatedAt] [datetime2](7) NOT NULL,
 CONSTRAINT [User_pkey] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[Profile] ADD  CONSTRAINT [Profile_isDefault_df]  DEFAULT ((0)) FOR [isDefault]
GO
ALTER TABLE [dbo].[Profile] ADD  CONSTRAINT [Profile_createdAt_df]  DEFAULT (getdate()) FOR [createdAt]
GO
ALTER TABLE [dbo].[Profile] ADD  CONSTRAINT [Profile_isPublic_df]  DEFAULT ((0)) FOR [isPublic]
GO
ALTER TABLE [dbo].[ProfileFollow] ADD  CONSTRAINT [ProfileFollow_createdAt_df]  DEFAULT (getdate()) FOR [createdAt]
GO
ALTER TABLE [dbo].[User] ADD  CONSTRAINT [User_createdAt_df]  DEFAULT (getdate()) FOR [createdAt]
GO
ALTER TABLE [dbo].[Profile]  WITH CHECK ADD  CONSTRAINT [Profile_userId_fkey] FOREIGN KEY([userId])
REFERENCES [dbo].[User] ([id])
ON UPDATE CASCADE
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[Profile] CHECK CONSTRAINT [Profile_userId_fkey]
GO
ALTER TABLE [dbo].[ProfileChannel]  WITH CHECK ADD  CONSTRAINT [ProfileChannel_profileId_fkey] FOREIGN KEY([profileId])
REFERENCES [dbo].[Profile] ([id])
ON UPDATE CASCADE
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[ProfileChannel] CHECK CONSTRAINT [ProfileChannel_profileId_fkey]
GO
ALTER TABLE [dbo].[ProfileFollow]  WITH CHECK ADD  CONSTRAINT [ProfileFollow_followerId_fkey] FOREIGN KEY([followerId])
REFERENCES [dbo].[User] ([id])
GO
ALTER TABLE [dbo].[ProfileFollow] CHECK CONSTRAINT [ProfileFollow_followerId_fkey]
GO
ALTER TABLE [dbo].[ProfileFollow]  WITH CHECK ADD  CONSTRAINT [ProfileFollow_profileId_fkey] FOREIGN KEY([profileId])
REFERENCES [dbo].[Profile] ([id])
ON UPDATE CASCADE
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[ProfileFollow] CHECK CONSTRAINT [ProfileFollow_profileId_fkey]
GO
ALTER TABLE [dbo].[ProfileKeyword]  WITH CHECK ADD  CONSTRAINT [ProfileKeyword_profileId_fkey] FOREIGN KEY([profileId])
REFERENCES [dbo].[Profile] ([id])
ON UPDATE CASCADE
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[ProfileKeyword] CHECK CONSTRAINT [ProfileKeyword_profileId_fkey]
GO
